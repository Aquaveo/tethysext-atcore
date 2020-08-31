"""
********************************************************************************
* Name: spatial_attributes_rws.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep


class SpatialAttributesRWS(SpatialResourceWorkflowStep):
    """
    Workflow step used for setting simple valued attributes on features.

    Options:
        geometry_source(varies): Geometry or parent to retrieve the geometry from. For passing geometry, use GeoJSON string.
        attributes(dict): Dictionary of param instances defining the attributes to be defined for each feature.
    """  # noqa: #501
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.map_workflows.SpatialAttributesMWV'
    TYPE = 'spatial_attributes_workflow_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'geometry_source': None,
            'attributes': {}
        })
        return default_options

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
