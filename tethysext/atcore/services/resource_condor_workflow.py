"""
********************************************************************************
* Name: resource_condor_workflow.py
* Author: gagelarsen
* Created On: December 11, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tethys_sdk.jobs import CondorWorkflowJobNode

from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.job_scripts import update_resource_status as update_resource_status_script


class ResourceCondorWorkflow(object):
    """
    Helper class that prepares and submits the new project upload jobs and workflow.
    """
    def __init__(self, app, user, workflow_name, workspace_path, resource_db_url, resource,
                 scheduler, job_manager, status_keys=None, engine_args={},**kwargs):
        """
        Constructor.

        Args:
            app (TethysApp): App class for the Tethys app.
            user (auth.User): Django user.
            workflow_name (str): Name of the job.
            workspace_path (str): Path to workspace to be used by job.
            resource_db_url (str): SQLAlchemy url to Resource database.
            resource (Resource): Instance of the Resource.
            scheduler (Scheduler): The condor scheduler for the application
            job_manager (JobManger): The condor job manager for the application.
            status_keys (list): One or more keys of statuses to check to determine resource status. The other jobs must update these statuses to one of the Resource.OK_STATUSES for the resource to be marked as SUCCESS.
            engine_args (dict): Optional arguments to pass to SQLAlchemy create_engine method.
        """  # noqa: E501
        self.app = app
        self.user = user
        self.job_name = workflow_name
        self.safe_job_name = ''.join(s if s.isalnum() else '_' for s in self.job_name)  #: Safe name with only A-Z 0-9
        self.workspace_path = workspace_path
        self.resource_db_url = resource_db_url
        self.resource_id = str(resource.id)
        self.resource_class_path = f'{resource.__module__}.{resource.__class__.__name__}'
        self.workflow = None
        self.scheduler = scheduler
        self.job_manager = job_manager
        self.status_keys = status_keys
        self.engine_args = engine_args

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
        status_keys = list() if self.status_keys is None else self.status_keys

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

        # Aggregate status key.
        for _, status_key in user_defined_jobs:
            status_keys.append(status_key)

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
                arguments=(
                    self.resource_db_url,
                    self.resource_id,
                    self.resource_class_path,
                    ','.join(status_keys)
                )
            ),
        )
        update_resource_status.save()

        # Set relationships
        for job, _ in user_defined_jobs:
            has_no_children = job.children_nodes.count() == 0
            if has_no_children:
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
            resource_db_engine = create_engine(self.resource_db_url, **self.engine_args)
            make_resource_db_session = sessionmaker(bind=resource_db_engine)
            resource_db_session = make_resource_db_session()
            resource = resource_db_session.query(Resource).get(self.resource_id)

            resource.set_status(Resource.ROOT_STATUS_KEY, Resource.STATUS_PENDING)
            resource_db_session.commit()

            self.prepare()
            self.workflow.execute()
        finally:
            resource_db_session and resource_db_session.close()
