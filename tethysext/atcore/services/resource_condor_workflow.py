"""
********************************************************************************
* Name: resource_condor_workflow.py
* Author: gagelarsen
* Created On: December 11, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tethys_sdk.jobs import CondorWorkflowJobNode

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.job_scripts import update_resource_status as update_resource_status_script


class ResourceCondorWorkflow(object):
    """
    Helper class that prepares and submits the new project upload jobs and workflow.
    """
    def __init__(self, user, workflow_name, workspace_path, resource_db_url, resource_id,
                 scheduler, job_manager, status_keys, **kwargs):
        """
        Constructor.

        Args:
            user(auth.User): Django user.
            workflow_name(str): Name of the job.
            workspace_path(str): Path to workspace to be used by job.
            resource_db_url(str): SQLAlchemy url to Resource database.
            resource_id(str): ID of associated resource.
        """  # noqa: E501
        self.user = user
        self.job_name = workflow_name
        self.safe_job_name = ''.join(s if s.isalnum() else '_' for s in self.job_name)  #: Safe name with only A-Z 0-9
        self.workspace_path = workspace_path
        self.resource_db_url = resource_db_url
        self.resource_id = resource_id
        self.workflow = None
        self.scheduler = scheduler
        self.job_manager = job_manager
        self.status_keys = status_keys
        self.input_archive_path = os.path.join(workspace_path, 'condor_upload.zip')

        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)

    def get_jobs(self):
        """
        Get CondorWorkflowJobNodes and the corresponding status key.

        Returns:
            list: A list of 2 tuples in the format [(CondorWorkflowJobNodes, 'status_key'), ...]
        """
        return []

    def prepare(self):
        """
        Prepares all workflow jobs for processing upload to database.
        """
        # Set parameters for HTCondor job
        self.workflow = self.job_manager.create_job(
            name=self.safe_job_name,
            user=self.user,
            job_type='CONDORWORKFLOW',
            max_jobs={'geoserver': 1},
            workspace=self.workspace_path,
            scheduler=self.scheduler
        )
        self.workflow.save()

        user_defined_jobs = self.get_jobs()

        input_archive_filename = os.path.basename(self.input_archive_path)

        # update_resource_status
        update_resource_status = CondorWorkflowJobNode(
            name='finalize',
            workflow=self.workflow,
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=(
                update_resource_status_script.__file__,
            ),
            attributes=dict(
                executable='update_resource_status.py',
                transfer_input_files=(f'../{input_archive_filename}',),
                arguments=(
                    self.resource_db_url,
                    self.resource_id,
                    ','.join(self.status_keys)
                )
            ),
        )
        update_resource_status.save()

        # Set relationships
        for job in user_defined_jobs:
            update_resource_status.add_parent(job)

        # add resource id to extended properties for filtering
        self.workflow.extended_properties['resource_id'] = str(self.resource_id)
        self.workflow.save()

    def run_job(self):
        """
        Executes the prepared job.
        """
        resource_db_session = None

        try:
            resource_db_engine = create_engine(self.resource_db_url)
            make_resource_db_session = sessionmaker(bind=resource_db_engine)
            resource_db_session = make_resource_db_session()
            resource = resource_db_session.query(Resource).get(self.resource_id)

            resource.set_status(Resource.ROOT_STATUS_KEY, Resource.STATUS_PENDING)
            resource_db_session.commit()

            self.prepare()
            self.workflow.execute()
        finally:
            resource_db_session and resource_db_session.close()
