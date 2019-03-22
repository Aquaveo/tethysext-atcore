"""
********************************************************************************
* Name: condor_workflow_manager.py
* Author: nswain
* Created On: March 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethys_sdk.compute import get_scheduler


class ResourceWorkflowCondorJobManager(object):
    """
    Helper class that prepares and submits condor workflows/jobs for resource workflows.
    """
    def __init__(self, session, model_db, resource_workflow_step, user, working_directory, app, scheduler_name,
                 jobs=None, input_files=None, *args):
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
        if not jobs or not all(isinstance(x, (dict, CondorWorkflowJobNode)) for x in jobs):
            raise ValueError('Argument "jobs" is not defined or empty. Must provide at least one CondorWorkflowJobNode '
                             'or equivalent dictionary.')

        # DB url for database containing the resource
        self.resource_db_url = str(session.get_bind().url)

        # DB URL for database containing the model database
        self.model_db_url = model_db.db_url

        # Important IDs
        self.resource_id = str(resource_workflow_step.workflow.resource.id)
        self.resource_workflow_id = str(resource_workflow_step.workflow.id)
        self.resource_workflow_step_id = str(resource_workflow_step.id)

        # Job Definition Variables
        self.jobs = jobs
        self.jobs_are_dicts = isinstance(jobs[0], dict)
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
        self.safe_job_name = ''.join(s for s in resource_workflow_step.name if s.isalnum())

        # Prepare standard arguments for all jobs
        self.job_args = [
            self.resource_db_url,
            self.model_db_url,
            self.resource_id,
            self.resource_workflow_id,
            self.resource_workflow_step_id,
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

    def _prepare(self):
        """
        Prepares all workflow jobs for processing upload to database.
        """
        # Prep
        scheduler = get_scheduler(self.scheduler_name)
        job_manager = self.app.get_job_manager()

        # Create Workflow
        self.workflow = job_manager.create_job(
            name=self.safe_job_name,
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

        # Preprocess jobs if they are dicts
        if self.jobs_are_dicts:
            self.jobs = self._build_job_nodes(self.jobs)

        # Add file names as args
        input_file_names = []
        for input_file in self.input_files:
            input_file_name = os.path.split(input_file)[1]
            input_file_names.append(input_file_name)
            self.job_args.append(input_file_name)

        # Parametrize each job
        for job in self.jobs:
            # Set arguments for each job
            job.set_attribute('arguments', self.job_args)

            # Add input files to transfer input files
            transfer_input_files = job.get_attribute('transfer_input_files') or []

            for input_file_name in input_file_names:
                transfer_input_files.append('../{}'.format(input_file_name))

            job.set_attribute('transfer_input_files', transfer_input_files)

            # Add additional remote input file
            remote_input_files = job.remote_input_files
            remote_input_files.extend(self.input_files)
            job.remote_input_files = remote_input_files

            # Save the job
            job.save()

        # Save Condor Workflow Job
        self.prepared = True

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

        for job_dict in job_dicts:
            # Pop-off keys to be handled separately
            attributes = job_dict.pop('attributes', {})

            job_dict.update({'workflow': self.workflow})

            job = CondorWorkflowJobNode(**job_dict)

            for attribute, value in attributes.items():
                job.set_attribute(attribute, value)

            job.save()
            jobs.append(job)

        return jobs

    def run_job(self):
        """
        Prepares and executes the job.

        Returns:
            str: UUID of the CondorWorkflow.
        """
        # Prepare
        if not self.prepared:
            self._prepare()

        # Execute
        self.workflow.execute()
        return str(self.workflow.id)
