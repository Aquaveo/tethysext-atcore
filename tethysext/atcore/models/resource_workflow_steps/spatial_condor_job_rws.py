"""
********************************************************************************
* Name: spatial_condor_job_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep


class SpatialCondorJobRWS(SpatialResourceWorkflowStep):
    """
    Workflow step used for reviewing previous step parameters and submitting processing jobs to Condor.

    Options:
        * **scheduler** (``str``): Name of the Condor scheduler to use.
        * **jobs** (``list<dict>``): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.
        * **workflow_kwargs** (``dict``): Additional keyword arguments to pass to the CondorWorkflow.

    **Parameters**:
        * None

    **Examples**:

        *statically defined jobs*:

        .. code-block:: python

            original_job = {
                'name': 'original_scenario',
                'condorpy_template_name': 'vanilla_transfer_files',
                'remote_input_files': [
                    os.path.join(job_executables_dir, 'workflows', 'detention_basin', 'run_original_scenario.py'),
                ],
                'attributes': {
                    'executable': 'run_original_scenario.py',
                    'transfer_output_files': [
                        'gssha_files',
                        'original_ohl_series.json'
                    ],
                    'request_cpus': cls.REQUEST_CPUS_PER_JOB
                },
            }

            latest_dt_job = {
                'name': 'latest_scenario',
                'condorpy_template_name': 'vanilla_transfer_files',
                'remote_input_files': [
                    os.path.join(job_executables_dir, 'workflows', 'detention_basin',
                                'run_latest_detention_basin_scenario.py'),
                ],
                'attributes': {
                    'executable': 'run_latest_detention_basin_scenario.py',
                    'transfer_output_files': [
                        'gssha_files',
                        'latest_ohl_series.json'
                    ],
                    'request_cpus': cls.REQUEST_CPUS_PER_JOB
                },
            }

            post_process_job = {
                'name': 'post_processing',
                'condorpy_template_name': 'vanilla_transfer_files',
                'remote_input_files': [
                    os.path.join(job_executables_dir, 'workflows', 'detention_basin', 'post_process.py'),
                ],
                'attributes': {
                    'executable': 'post_process.py',
                    'transfer_output_files': [],
                    'transfer_input_files': [
                        '../original_scenario/original_ohl_series.json',
                        '../latest_scenario/latest_ohl_series.json',
                        '../pre_detention_basin_scenario/pre_detention_basin_ohl_series.json',
                        '../post_detention_basin_scenario/post_detention_basin_ohl_series.json',
                    ],
                    'request_cpus': cls.REQUEST_CPUS_PER_JOB
                },
                'parents': [original_job['name'], latest_dt_job['name']]
            }

            step6 = SpatialCondorJobRWS(
                name='Preliminary Run',
                order=60,
                help='Review input and then press the Run button to run the model. '
                    'Press Next after the model execution completes to continue.',
                options={
                    'scheduler': app.SCHEDULER_NAME,
                    'jobs': [original_job, latest_dt_job, pre_dt_hydrograph_job, post_dt_hydrograph_job, post_process_job],
                    'working_message': 'Please wait for the model to finish running before proceeding.',
                    'error_message': 'An error occurred with the run. Please adjust your input and try running '
                                    'the model again.',
                    'pending_message': 'Please run the model to continue.'
                },
                geoserver_name=geoserver_name,
                map_manager=map_manager,
                spatial_manager=spatial_manager,
                active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN]
            )

        *dynamically defined jobs*:

        .. code-block:: python

            def build_compute_inflows_jobs_callback(condor_workflow):
                from django.conf import settings
                proj_default = '/var/lib/condor/micromamba/envs/tethys/share/proj'
                proj_lib = os.environ.get('CONDOR_PROJ_LIB', datadir.get_data_dir()) if settings.DEBUG else proj_default

                jobs = []
                job_executables_dir = condor_workflow.app.get_job_executables_dir()
                resource_workflow = condor_workflow.resource_workflow

                # Get the selected scenarios
                scenarios_step = resource_workflow.get_step_by_name('Select Flow Simulation Options')
                form_values_param = scenarios_step.get_parameter('form-values')
                scenarios = form_values_param['storm_type']

                transfer_input_files = []
                gssha_job_names = []
                for scenario in scenarios:
                    idx = scenario.rfind(':')  # Use rfind in case scenario name includes a colon
                    scenario_name = scenario[:idx]
                    scenario_fname = safe_str(scenario_name)
                    scenario_id = scenario[idx+1:]
                    job_name = f'run_{scenario_fname}'
                    output_filename = f'{scenario_id}_ohl_series.json'

                    # Set up the job for the scenario
                    job = {
                        'name': job_name,
                        'condorpy_template_name': 'vanilla_transfer_files',
                        'category': 'agwa_get_discharge_flow',
                        'remote_input_files': [
                            os.path.join(job_executables_dir, 'workflows', 'grab_discharge', 'run_scenario.py'),
                        ],
                        'attributes': {
                            'executable': 'run_scenario.py',
                            'arguments': [scenario_fname, scenario_id],
                            'transfer_output_files': [
                                # 'gssha_files',
                                output_filename,
                            ],
                            'environment': f'PROJ_LIB={proj_lib}',
                            'request_cpus': GrabDischargeWorkflow.REQUEST_CPUS_PER_JOB
                        }
                    }

                    # Store the input
                    transfer_input_files.append(f'../{job_name.replace(" ", "_")}/{output_filename}')
                    gssha_job_names.append(job['name'])
                    jobs.append(job)

                post_process_job = {
                    'name': 'post_processing',
                    'condorpy_template_name': 'vanilla_transfer_files',
                    'remote_input_files': [
                        os.path.join(job_executables_dir, 'workflows', 'grab_discharge', 'post_process_flow.py'),
                    ],
                    'attributes': {
                        'executable': 'post_process_flow.py',
                        'transfer_output_files': [],
                        'transfer_input_files': transfer_input_files,
                        'request_cpus': GrabDischargeWorkflow.REQUEST_CPUS_PER_JOB,
                    },
                    'parents': gssha_job_names,
                }

                return jobs + [post_process_job]

            compute_flows_step = SpatialCondorJobRWS(
                name='Compute Flows',
                order=30,
                help='Review input and then press the Run button to run the model and compute inflows for each point. '
                    'Press Next after the model execution completes to continue.',
                options={
                    'scheduler': app.SCHEDULER_NAME,
                    'jobs': build_compute_inflows_jobs_callback,
                    'workflow_kwargs': {
                        'max_jobs': {'agwa_get_discharge_flow': cls.MAX_JOBS_FLOW}
                    },
                    'working_message': 'Please wait for the model to finish running before proceeding.',
                    'error_message': 'An error occurred with the run. Please adjust your input and try running '
                                    'the model again.',
                    'pending_message': 'Please run the model to continue.'
                },
                geoserver_name=geoserver_name,
                map_manager=map_manager,
                spatial_manager=spatial_manager,
                active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN]
            )
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialCondorJobMWV'
    TYPE = 'spatial_condor_job_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'scheduler': '',
            'jobs': [],
            'workflow_kwargs': {},
            'working_message': '',
            'error_message': '',
            'pending_message': '',
            'lock_workflow_on_job_submit': False,
            'lock_resource_on_job_submit': False,
            'unlock_workflow_on_job_submit': False,
            'unlock_resource_on_job_submit': False,
            'lock_workflow_on_job_complete': False,
            'lock_resource_on_job_complete': False,
            'unlock_workflow_on_job_complete': False,
            'unlock_resource_on_job_complete': False
        })
        return default_options

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return {}

    def validate(self):
        """
        Validates parameter values of this this step.

        Returns:
            bool: True if data is valid, else Raise exception.

        Raises:
            ValueError
        """
        # Run super validate method first to perform built-in checks (e.g.: Required)
        super().validate()
