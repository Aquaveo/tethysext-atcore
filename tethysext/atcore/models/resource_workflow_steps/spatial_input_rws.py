"""
********************************************************************************
* Name: spatial_input_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep


class SpatialInputRWS(SpatialResourceWorkflowStep):
    """
    Workflow step used for retrieving simple spatial user input (points, lines, polygons).

    Options:
        shapes(list): The types of shapes to allow. Any combination of 'points', 'lines', 'polygons', and/or 'extents'.
        singular_name(str): Name to use when referring to a single feature in other areas of the user interface (e.g. "Detention Basin"). 
        plural_name(str): Name to use when referring to multiple features in other areas of the user interface (e.g. "Detention Basins").
        allow_shapefile(bool): Allow shapfile upload as spatial input. Defaults to True.
        allow_drawing(bool): Allow manually drawing shapes. Defaults to True.
        snapping_enabled(bool): Enabled snapping when drawing features. Defaults to True.
        snapping_layer(dict): Specify a layer to snap to. Create a 1-dict where the key is the dot-path to the layer attribute to use in comparison  and the value is the value to match (e.g. {'data.layer_id': 10}).
        snapping_options(dict): Supported options include edge, vertex, pixelTolerance. See: https://openlayers.org/en/latest/apidoc/module-ol_interaction_Snap.html
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialInputMWV'
    TYPE = 'spatial_input_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        return {
            'shapes': ['points', 'lines', 'polygons', 'extents'],
            'singular_name': 'Feature',
            'plural_name': 'Features',
            'allow_shapefile': True,
            'allow_drawing': True,
            'snapping_enabled': True,
            'snapping_layer': {},
            'snapping_options': {}
        }

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

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