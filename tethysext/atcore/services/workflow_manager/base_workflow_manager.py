import os

from tethys_compute.models import CondorWorkflowJobNode
from tethysext.atcore.utilities import generate_geoserver_urls


class BaseWorkflowManager(object):
    ATCORE_EXECUTABLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                         'resources', 'resource_workflows')

    def __init__(self, session, model_db, resource_workflow_step, user, working_directory, app, scheduler_name=None,
                 jobs=None, job_script=None, input_files=None, gs_engine=None, *args):
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

        # Job Definition Variables
        self.jobs = jobs
        self.job_script = job_script
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
        ]

        # Add custom args
        self.job_args.extend(self.custom_job_args)

        # State variables
        self.workflow = None
        self.prepared = False
        self.workspace_initialized = False
        self._workspace_path = None

    def _initialize_workspace(self):
        """
        Create workspace if it doesn't exist.
        """
        # Create job directory if it doesn't exist already
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        self.workspace_initialized = True

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

    def prepare(self):
        raise NotImplementedError

    def run_job(self):
        """
        Prepares and executes the job.

        Returns:
            str: UUID of the Workflow/Job.
        """
        # Prepare
        if not self.prepared:
            self.prepare()

        # Execute
        self.workflow.execute()
        return str(self.workflow.id)
