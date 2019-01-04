"""
********************************************************************************
* Name: polygon_step.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy import Column, PickleType
from tethysext.atcore.models.app_users import ResourceWorkflowStep


class SpatialInputResourceWorkflowStep(ResourceWorkflowStep):
    """
    Workflow step used for retrieving simple spatial user input (points, lines, polygons).

    Options:
        shapes(list): The types of shapes to allow. Any combination of 'points', 'lines', 'polygons', and/or 'extents'.
        allow_shapefile(bool): Allow shapfile upload as spatial input. Defaults to True.
        allow_drawing(bool): Allow manually drawing shapes. Defaults to True.
    """
    TYPE = 'spatial_input_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    def __init__(self, geoserver_name, map_manager, spatial_manager, *args, **kwargs):
        """

        Args:
            geoserver_name:
            map_manager:
            spatial_manager:
            *args:
            **kwargs:
        """
        # Defaults
        self.options = {
            'shapes': ['points', 'lines', 'polygons', 'extents'],
            'allow_shapefile': True,
            'allow_drawing': True
        }
        self.controller_path = 'tethysext.atcore.controllers.resource_workflows.MapWorkflowView'
        self.controller_kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            '_SpatialManager': spatial_manager
        }

        super().__init__(*args, **kwargs)

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Args:
            step_options(dict): Options for this step.

        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'geometry': {
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
        #
        # polygon = self._parameters['polygon']
        # value = polygon['value']
        #
        # # Validate polygon parameter
        #
        # # Not list
        # if not isinstance(value, list):
        #     raise ValueError('The "polygon" parameter must be a list<2-list<number>>.')
        #
        # # Not 2-list inside list
        # for item in value:
        #     if not isinstance(item, list) or len(item) != 2:
        #         raise ValueError('The "polygon" parameter must be a list<2-list<number>>.')
        #
        # # Not number-like in 2-list
        # for x, y in value:
        #     try:
        #         float(x)
        #         float(y)
        #     except ValueError:
        #         raise ValueError('The "polygon" parameter must contain only numbers.')
        #
        # # Not enough points to make a polygon (3+)
        # if len(value) < 4:  # Last coordinate is repeated, so a 3-point polygon has 4-points
        #     raise ValueError('At least 3 points required to create a polygon: {} given.'.format(len(value) - 1))
        #
        # # Last value not repeated
        # if value[0] != value[-1]:
        #     raise ValueError('The first coordinate of "polygon" parameter must be repeated at the end.')
