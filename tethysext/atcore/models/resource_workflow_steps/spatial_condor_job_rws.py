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
        scheduler(str): Name of the Condor scheduler to use.
        jobs(list<dict>): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialCondorJobMWV'
    TYPE = 'spatial_condor_job_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        return {
            'scheduler': '',
            'jobs': [],
        }

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
