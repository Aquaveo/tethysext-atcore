"""
********************************************************************************
* Name: spatial_input_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import param
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
        default_options = super().default_options
        default_options.update({
            'shapes': ['points', 'lines', 'polygons', 'extents'],
            'singular_name': 'Feature',
            'plural_name': 'Features',
            'allow_shapefile': True,
            'allow_drawing': True,
            'snapping_enabled': True,
            'snapping_layer': {},
            'snapping_options': {},
            'attributes': None
        })
        return default_options

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

        attributes_param = self.options.get('attributes', None)

        # Skip if no attributes option given
        if attributes_param is None:
            return True

        # Iterate through each geometry defined by the user and validate attributes
        geometry = self.get_parameter('geometry')

        for feature in geometry.get('features', []):
            properties = feature.get('properties', {})
            self.validate_feature_attributes(properties)

        return True

    def validate_feature_attributes(self, attributes):
        """
        Validate attribute values of a feature against the given param-based attributes definition.

        Args:
            attributes(dict<attribute,value>): The attributes/properties of the feature to validate.

        Returns:
            bool: True if data is valid, else Raise exception.

        Raises:
            ValueError: If validation fails, a ValueError is raised with appropriate message to display to the user.
        """  # noqa: E501
        # Get attributes param object if not given.
        attributes_definition = self.options.get('attributes', None)

        # Skip if no attributes definition provided
        if attributes_definition is None:
            return True

        all_defined_attributes = attributes_definition.param.params()
        null_equivalents = ['']
        validation_errors = []

        # Validate required attributes that are not included in the given attributes
        for attribute_name, defined_attribute in all_defined_attributes.items():
            # Validate parameters that are "Required" but have no value
            value_required = not defined_attribute.allow_None
            attribute_title = attribute_name.replace("_", " ").title()

            # Skip attributes that are not given, raising a validation error if it is required
            if attribute_name not in attributes:
                if value_required:
                    validation_errors.append(f'{defined_attribute.label} is required.')
                continue

            # Get the value
            value = attributes[attribute_name]

            # Convert null equivalent values to None as a way to use "allow_None" attribute param.Parameters
            val = None if value in null_equivalents else value

            if val is None and value_required:
                validation_errors.append(f'{defined_attribute.label} is required.')
                continue

            # Cast values to numbers if definition is a number field
            try:
                if isinstance(defined_attribute, param.Integer):
                    val = int(val)
                elif isinstance(defined_attribute, (param.Number, param.Magnitude)):
                    val = float(val)
            except TypeError:
                validation_errors.append(f'{attribute_title} must be a number.')
                continue

            # Convert "on" value to boolean for Boolean fields
            if isinstance(defined_attribute, param.Boolean):
                val = val in ('on', 'checked')

            # Validate by assigning attribute to Parameterized object
            try:
                setattr(attributes_definition, attribute_name, val)
            except ValueError as e:
                # Rewrite the message to something the user will understand
                msg = self._colloquialize_validation_error(str(e), attribute_name, attribute_title)
                validation_errors.append(msg)

        if validation_errors:
            msg = '\n'.join(validation_errors)
            raise ValueError(msg)

        return True

    @staticmethod
    def _colloquialize_validation_error(message, attribute_name, attribute_title):
        """
        Translate ValueError messages given by param to something the user can understand (e.g.: "Parameter 'integer' must be at least 0" to "Integer must be at least 0.").
        Args:
            message(str): The validation error message raised by param.
            attribute_name(str): Name of the attribute/param property (e.g.: "location_name").
            attribute_title(str): Title version of the attribute_name (e.g.: "Location Name").

        Returns:
            str: translated message
        """  # noqa: E501
        if attribute_name in message:
            # Attribute name is in message, attempt to replace with attribute title
            # e.g.: "Parameter 'integer' must be at least 0." to "Integer must be at least 0."
            dq_attribute_name = f'"{attribute_name}"'  #: attribute_name wrapped in double quotes
            sq_attribute_name = f"'{attribute_name}'"  #: attribute_name wrapped in single quotes

            if dq_attribute_name in message:
                msg_parts = message.split(dq_attribute_name)
            elif sq_attribute_name in message:
                msg_parts = message.split(sq_attribute_name)
            else:
                msg_parts = message.split(attribute_name)

            if '' not in msg_parts or msg_parts[0] == '' and msg_parts[-1] == '':
                # attribute name not at beginning or end of message, could be in message multiple times
                # e.g.: "Parameter integer must an integer and be greater than 0."
                # or "Parameter integer must be greater than 0."
                # or "integer must be an integer"
                message = attribute_title + attribute_name.join(msg_parts[1:])

            elif msg_parts[0] == '':
                # attribute name at beginning only
                # e.g.: "integer must be at most 10"
                message = attribute_title + msg_parts[1]

            elif msg_parts[-1] == '':
                # attribute name at end only
                # e.g.: "Bad value for field integer"
                message = msg_parts[0] + attribute_title

        else:
            # Attribute name is not in message
            # e.g.: "An unexpected message was given."
            message = ': '.join([attribute_title, message])

        return message
