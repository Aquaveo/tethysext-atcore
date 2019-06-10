"""
********************************************************************************
* Name: map_workflow_view.py
* Author: nswain
* Created On: November 21, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import abc
import logging
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep

log = logging.getLogger(__name__)


class MapWorkflowView(MapView, ResourceWorkflowView):
    """
    Controller for a map view with workflows integration.
    """
    template_name = 'atcore/resource_workflows/map_workflow_view.html'
    valid_step_classes = [ResourceWorkflowStep]

    def get_context(self, request, session, resource, context, model_db, workflow_id, step_id, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): the session.
            resource(Resource): the resource for this request.
            context(dict): The context dictionary.
            model_db(ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        map_context = MapView.get_context(
            self=self,
            request=request,
            session=session,
            resource=resource,
            context=context,
            model_db=model_db,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        workflow_context = ResourceWorkflowView.get_context(
            self=self,
            request=request,
            session=session,
            resource=resource,
            context=context,
            model_db=model_db,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        # Combine contexts
        map_context.update(workflow_context)

        return map_context

    @staticmethod
    def set_feature_selection(map_view, enabled=True):
        """
        Set whether features are selectable or not.
        Args:
            map_view(MapView): The MapView gizmo options object.
            enabled(bool): True to enable selection, False to disable it.
        """
        # Disable feature selection on all layers so it doesn't interfere with drawing
        for layer in map_view.layers:
            layer.feature_selection = enabled
            layer.editable = enabled

    @abc.abstractmethod
    def process_step_options(self, request, session, context, resource, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            resource(Resource): the resource for this request.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
