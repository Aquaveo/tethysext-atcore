"""
********************************************************************************
* Name: spatial_condor_job_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class SpatialCondorJobRWS(ResourceWorkflowStep):
    """
    Workflow step used for reviewing previous step parameters and submitting processing jobs to Condor.

    Options:
        scheduler(str): Name of the Condor scheduler to use.
        jobs(list<dict>): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.
    """  # noqa: #501
    TYPE = 'spatial_condor_job_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    def __init__(self, geoserver_name, map_manager, spatial_manager, *args, **kwargs):
        """
        Constructor.

        Args:
            geoserver_name(str): Name of geoserver setting to use.
            map_manager(MapManager): Instance of MapManager to use for the map view.
            spatial_manager(SpatialManager): Instance of SpatialManager to use for the map view.
        """
        self.controller_path = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialCondorJobMWV'
        self.controller_kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            '_SpatialManager': spatial_manager
        }

        super().__init__(*args, **kwargs)

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
