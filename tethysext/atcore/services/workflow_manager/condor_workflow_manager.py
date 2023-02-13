"""
********************************************************************************
* Name: condor_workflow_manager.py
* Author: nswain
* Created On: March 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import inspect
import logging
import os
from tethys_sdk.jobs import CondorWorkflowJobNode
from .base_workflow_manager import BaseWorkflowManager
from tethysext.atcore.utilities import generate_geoserver_urls
from tethys_apps.exceptions import TethysAppSettingDoesNotExist

log = logging.getLogger(f'tethys.{__name__}')


class ResourceWorkflowCondorJobManager(BaseWorkflowManager):
    """
    Helper class that prepares and submits condor workflows/jobs for resource workflows.
    """
    ATCORE_EXECUTABLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                         'resources', 'resource_workflows')

    def __init__(self, session, model_db, resource_workflow_step, user, working_directory, app, scheduler_name,
                 jobs=None, input_files=None, gs_engine=None, *args):
        """
        Constructor.

        Args:
            session(sqlalchemy.orm.Session): An SQLAlchemy session bound to the resource workflow.
            model_db(ModelDatabase): ModelDatabase instance bound to model database.
            resource_workflow_step(atcore.models.app_users.ResourceWorkflowStep): Instance of ResourceWorkflowStep. Note: Must have active session (i.e. not closed).
            user(auth.User): The Django user submitting the job.
            working_directory(str): Path to users's workspace.
            app(TethysAppBase): Class or instance of an app.
            scheduler_name(str): Name of the condor scheduler to use.
            jobs(list<CondorWorkflowJobNode or dict>): List of CondorWorkflowJobNodes to run.
            input_files(list<str>): List of paths to files to sends as inputs to every job. Optional.
        """  # noqa: E501
        self.validate_jobs(jobs)

        # DB url for database containing the resource
        self.resource_db_url = str(session.get_bind().url)

        # DB URL for database containing the model database
        if model_db:
            try:
                self.model_db_url = model_db.db_url
            except TethysAppSettingDoesNotExist:
                log.warning('no model database found')
                self.model_db_url = None
        else:
            log.warning('no model database provided')
            self.model_db_url = None

        # Serialize GeoServer Connection
        self.gs_private_url = ''
        self.gs_public_url = ''
        if gs_engine is not None:
            self.gs_private_url, self.gs_public_url = generate_geoserver_urls(gs_engine)

        # Important IDs
        self.resource_id = str(resource_workflow_step.workflow.resource.id)
        self.resource_name = resource_workflow_step.workflow.resource.name
        self.resource_workflow_id = str(resource_workflow_step.workflow.id)
        self.resource_workflow_name = resource_workflow_step.workflow.name
        self.resource_workflow_type = resource_workflow_step.workflow.DISPLAY_TYPE_SINGULAR
        self.resource_workflow_step_id = str(resource_workflow_step.id)
        self.resource_workflow_step_name = resource_workflow_step.name

        # Get Path to Resource and Workflow Classes
        self.resource_class = self._get_class_path(resource_workflow_step.workflow.resource)
        self.workflow_class = self._get_class_path(resource_workflow_step.workflow)

        # Job Definition Variables
        self.jobs = jobs
        self.session = session
        self.user = user
        self.working_directory = working_directory
        self.app = app
        self.scheduler_name = scheduler_name
        if input_files is None:
            self.input_files = []
        else:
            self.input_files = input_files
        self.custom_job_args = args

        #: Safe name with only A-Z 0-9
        self.safe_job_name = ''.join(s if s.isalnum() else '_' for s in self.resource_workflow_step_name)

        # Prepare standard arguments for all jobs
        self.job_args = [
            self.resource_db_url,
            self.model_db_url,
            self.resource_id,
            self.resource_workflow_id,
            self.resource_workflow_step_id,
            self.gs_private_url,
            self.gs_public_url,
            self.resource_class,
            self.workflow_class
        ]

        # Add custom args
        self.job_args.extend(self.custom_job_args)

        # State variables
        self.workflow = None
        self.prepared = False
        self.workspace_initialized = False
        self._workspace_path = None

    @property
    def workspace(self):
        """
        Workspace path property.
        Returns:
            str: Path to workspace for this workflow
        """
        if self._workspace_path is None:
            self._workspace_path = os.path.join(
                self.working_directory,
                str(self.resource_workflow_id),
                str(self.resource_workflow_step_id),
                self.safe_job_name
            )

            # Initialize workspace
            if not self.workspace_initialized:
                self._initialize_workspace()

        return self._workspace_path

    def _initialize_workspace(self):
        """
        Create workspace if it doesn't exist.
        """
        # Create job directory if it doesn't exist already
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        self.workspace_initialized = True

    @staticmethod
    def _get_class_path(obj):
        """
        Derive the dot path of the class of a given object class.
        """
        module = obj.__class__.__module__
        if module is None or module == str.__class__.__module__:
            return obj.__class__.__name__  # Avoid reporting __builtin__
        else:
            return module + '.' + obj.__class__.__name__

    def prepare(self):
        """
        Prepares all workflow jobs for processing upload to database.

        Returns:
            int: the job id.
        """
        # Prep
        scheduler = self.app.get_scheduler(self.scheduler_name)
        # TODO: Cleanup other jobs associated with this workflow...
        job_manager = self.app.get_job_manager()

        # Create Workflow
        self.workflow = job_manager.create_job(
            name=self.safe_job_name,
            description='{}: {}'.format(self.resource_workflow_type, self.resource_workflow_step_name),
            job_type='CONDORWORKFLOW',
            workspace=self.workspace,
            user=self.user,
            scheduler=scheduler,
            extended_properties={
                'resource_id': self.resource_id,
                'resource_workflow_id': self.resource_workflow_id,
                'resource_workflow_step_id': self.resource_workflow_step_id,
            }
        )

        # Save the workflow
        self.workflow.save()

        # Preprocess jobs if they are dicts or a callback function
        if inspect.isfunction(self.jobs):
            cur_jobs = self.jobs(self)
            self.validate_jobs(cur_jobs)  # Validate again (needed if self.jobs was a callback function)
        else:
            cur_jobs = self.jobs
        if isinstance(cur_jobs[0], dict):
            # Jobs are dicts
            cur_jobs = self._build_job_nodes(cur_jobs)
        self.jobs = cur_jobs

        # Add file names as args
        input_file_names = []
        for input_file in self.input_files:
            input_file_name = os.path.split(input_file)[1]
            input_file_names.append(input_file_name)
            self.job_args.append(input_file_name)

        # Parametrize each job
        for job in self.jobs:
            # Set arguments for each job
            existing_job_args = job.get_attribute('arguments')
            if existing_job_args:
                existing_job_args = existing_job_args.split()
            current_job_args = self.job_args + (existing_job_args if existing_job_args else [])
            job.set_attribute('arguments', current_job_args)

            # Add input files to transfer input files
            transfer_input_files_str = job.get_attribute('transfer_input_files') or ''
            transfer_input_files = transfer_input_files_str.split(',')

            for input_file_name in input_file_names:
                transfer_input_files.append('../{}'.format(input_file_name))

            job.set_attribute('transfer_input_files', transfer_input_files)

            # Add additional remote input file
            remote_input_files = job.remote_input_files
            remote_input_files.extend(self.input_files)
            job.remote_input_files = remote_input_files

            # Save the job
            job.save()

        # Create update status job
        update_status_job = CondorWorkflowJobNode(
            name='finalize',  # Better for display name
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(self.ATCORE_EXECUTABLE_DIR, 'update_status.py'),
            ],
            workflow=self.workflow
        )

        update_status_job.set_attribute('executable', 'update_status.py')
        update_status_job.set_attribute('arguments', self.job_args)
        update_status_job.set_attribute('transfer_input_files', ['../workflow_params.json'])

        update_status_job.save()

        # Bind update_status job only to terminal nodes in the workflow (jobs without children)
        for job in self.jobs:
            if len(job.children_nodes.select_subclasses()) <= 0:
                update_status_job.add_parent(job)

        self.jobs.append(update_status_job)

        update_status_job.save()

        # Save Condor Workflow Job
        self.prepared = True

        return self.workflow.id

    def _build_job_nodes(self, job_dicts):
        """
        Build CondorWorkflowJobNodes from the job_dicts provided.

        Args:
            job_dicts(list<dicts>): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.

        Returns:
            list<CondorWorkflowJobNodes>: the job nodes.
        """
        from tethys_sdk.jobs import CondorWorkflowJobNode

        jobs = []
        job_map = {}

        # Create all the jobs
        for job_dict in job_dicts:
            # Pop-off keys to be handled separately
            parents = job_dict.pop('parents', [])
            attributes = job_dict.pop('attributes', {})

            job_dict.update({'workflow': self.workflow})

            job = CondorWorkflowJobNode(**job_dict)

            for attribute, value in attributes.items():
                job.set_attribute(attribute, value)

            job.save()
            jobs.append(job)

            # For mapping relationships
            job_map[job.name] = {'job': job, 'parents': parents}

        # Set Parent Relationships
        for job in jobs:
            for parent_name in job_map[job.name]['parents']:
                job.add_parent(job_map[parent_name]['job'])

            job.save()

        return jobs

    def run_job(self):
        """
        Prepares and executes the job.

        Returns:
            str: UUID of the CondorWorkflow.
        """
        # Prepare
        if not self.prepared:
            self.prepare()

        # Execute
        self.workflow.execute()
        return str(self.workflow.id)

    def validate_jobs(self, jobs):
        """
        Validates that the jobs are defined (not empty) and are a CondorWorkflowJobNode or equivalent dicaiontry.

        Args:
            jobs(list<CondorWorkflowJobNode or dict>): List of CondorWorkflowJobNodes to run.
        """
        if (
            not jobs or
            (not inspect.isfunction(jobs) and not all(isinstance(x, (dict, CondorWorkflowJobNode)) for x in jobs))
        ):
            raise ValueError('Given "jobs" is not defined or empty. Must provide at least one '
                             'CondorWorkflowJobNode or equivalent dictionary.')
