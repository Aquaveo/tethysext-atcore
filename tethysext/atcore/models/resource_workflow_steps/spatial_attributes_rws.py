"""
********************************************************************************
* Name: spatial_attributes_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS


class SpatialAttributesRWS(SpatialInputRWS):
    """
    Workflow step used for setting simple valued attributes on features.

    Options:
        geometry(varies): Geometry or parent to retrieve the geometry from. For passing geometry, use GeoJSON string.
        attributes(dict): Dictionary of param instances defining the attributes to be defined for each feature.
    """  # noqa: #501
    TYPE = 'spatial_attributes_workflow_step'

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
        super().__init__(
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            *args, **kwargs
        )
        self.controller_path = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialAttributesMWV'

    @property
    def default_options(self):
        return {
            'geometry_source': None,
            'attributes': {}
        }

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Args:
            step_options(dict): Options for this step.

        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'attributed_geometry': {
                'help': 'Valid GeoJSON representing geometry input by user.',
                'value': None,
                'required': False
            },
        }

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
