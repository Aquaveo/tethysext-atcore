"""
********************************************************************************
* Name: spatial_input_mwv
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.app_users.resource_workflow_steps import SpatialAttributesRWS


class SpatialAttributesMWV(MapWorkflowView):

    def validate_step(self, request, session, current_step, previous_step, next_step):
        """
        Validate the step being used for this view. Raises TypeError if current_step is invalid.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.

        Raises:
            TypeError: if step is invalid.
        """
        # Initialize drawing tools for spatial input parameter types.
        if not isinstance(current_step, SpatialAttributesRWS):
            raise TypeError('Invalid step type for view: {}. Must be a SpatialAttributesRWS.'.format(
                type(current_step))
            )

    def process_step_options(self, request, session, context, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
        pass
