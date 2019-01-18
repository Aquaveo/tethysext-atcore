"""
********************************************************************************
* Name: polygon_step.py
* Author: nswain
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethysext.atcore.models.app_users.resource_workflow_steps import SpatialInputResourceWorkflowStep


class SpatialAttributesStep(SpatialInputResourceWorkflowStep):
    """
    Workflow step used for retrieving simple spatial user input (points, lines, polygons).

    Options:
        geometry(varies): Geometry or step to retrieve the geometry from. For passing geometry, use GeoJSON string. For specifying a step to use, enter the id of the step or use the keyword 'previous' to use the previous step.
        attributes(dict): Dictionary of param instances defining the attributes to be defined for each feature.
    """  # noqa: #501
    TYPE = 'spatial_attributes_step'

    __mapper_args__ = {
        'polymorphic_identity': TYPE
    }

    @property
    def default_options(self):
        return {
            'geometry': None,
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
