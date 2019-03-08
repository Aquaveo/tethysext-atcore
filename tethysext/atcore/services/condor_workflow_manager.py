"""
********************************************************************************
* Name: condor_workflow_manager.py
* Author: nswain
* Created On: March 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import json
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethys_sdk.compute import get_scheduler


class CondorWorkflowJobManager(object):
    """
    Helper class that prepares and submits condor workflows.
    """
    def __init__(self, session, model_db, resource_workflow_step, jobs, user, working_directory, app, scheduler_name,
                 input_files, *args):
        """
        Constructor.

        Args:
            session(sqlalchemy.orm.Session): An SQLAlchemy session bound to the resource workflow.
            model_db(ModelDatabase): ModelDatabase instance bound to model database.
            resource_workflow_step(atcore.models.app_users.ResourceWorkflowStep): Instance of ResourceWorkflowStep. Note: Must have active session (i.e. not closed).
            jobs(list<CondorWorkflowJobNode>): List of CondorWorkflowJobNodes to run. 
            user(auth.User): The Django user submitting the job.
            working_directory(str): Path to users's workspace.
            app(TethysAppBase): Class or instance of an app.
            scheduler_name(str): Name of the condor scheduler to use.
            input_files(list<str>): List of paths to files to include as job inputs.
        """  # noqa: E501
        # DB url for database containing the resource
        self.resource_db_url = str(session.get_bind().url)

        # DB URL for database containing the model database
        self.model_db_url = model_db.db_url

        # Important IDs
        self.resource_id = resource_workflow_step.workflow.resource.id
        self.resource_workflow_id = resource_workflow_step.workflow.id
        self.resource_workflow_step_id = resource_workflow_step.id

        # Job Definition Variables
        self.jobs = jobs
        self.user = user
        self.working_directory = working_directory
        self.app = app
        self.scheduler_name = scheduler_name
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

        # Add file names as args
        for input_file in self.input_files:
            self.job_args.append(os.path.split(input_file)[1])

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

    def prepare(self):
        """
        Prepares all workflow jobs for processing upload to database.
        """
        # Prep
        scheduler = get_scheduler(self.scheduler_name)
        job_manager = self.app.get_job_manager()

        # Parameterize each job
        for job in self.jobs:
            # Set arguments for each job
            job.set_attribute('arguments', self.job_args)
            # Add additional remote input file
            job.remote_input_files.extend(self.input_files)

        # Create Workflow
        self.workflow = job_manager.create_job(
            name=self.safe_job_name,
            job_type='CONDORWORKFLOW',
            workspace=self.workspace,
            jobs=self.jobs,
            user=self.user,
            scheduler=scheduler,
            extended_properties={
                'resource_id': self.resource_id,
                'resource_workflow_id': self.resource_workflow_id,
                'resource_workflow_step_id': self.resource_workflow_step_id,
            }
        )

        # Save Condor Workflow Job
        self.workflow.save()
        self.prepared = True

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
