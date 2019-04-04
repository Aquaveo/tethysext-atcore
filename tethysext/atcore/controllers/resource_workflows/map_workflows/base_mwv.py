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
from django.shortcuts import redirect, reverse
from django.contrib import messages
from tethys_apps.utilities import get_active_app
from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController
from tethysext.atcore.controllers.map_view import MapView
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_controller
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep

log = logging.getLogger(__name__)


class MapWorkflowView(MapView, AppUsersResourceWorkflowController, metaclass=abc.ABCMeta):
    """
    Controller for a map view with workflows integration.
    """
    template_name = 'atcore/resource_workflows/map_workflow_view.html'
    valid_step_classes = [ResourceWorkflowStep]

    def get_context(self, request, session, resource, context, model_db, map_manager, workflow_id, step_id,
                    *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        workflow = self.get_workflow(request, workflow_id, session=session)
        current_step = self.get_step(request, step_id=step_id, session=session)
        previous_step, next_step = workflow.get_adjacent_steps(current_step)

        # Hook for validating the current step
        self.validate_step(
            request=request,
            session=session,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )

        # Handle any status message from previous requests
        status_message = current_step.get_attribute(current_step.ATTR_STATUS_MESSAGE)
        if status_message:
            step_status = current_step.get_status(current_step.ROOT_STATUS_KEY)
            if step_status in (current_step.STATUS_ERROR, current_step.STATUS_FAILED):
                messages.error(request, status_message)
            elif step_status in (current_step.STATUS_COMPLETE,):
                messages.success(request, status_message)
            else:
                messages.info(request, status_message)

        # Hook for handling step options
        self.process_step_options(
            request=request,
            session=session,
            context=context,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )

        # Build step cards
        previous_status = None
        steps = []

        for workflow_step in workflow.steps:
            step_status = workflow_step.get_status(workflow_step.ROOT_STATUS_KEY)
            step_in_progress = step_status != workflow_step.STATUS_PENDING and step_status is not None
            create_link = previous_status == workflow_step.STATUS_COMPLETE \
                or previous_status is None \
                or step_in_progress

            card_dict = {
                'id': workflow_step.id,
                'help': workflow_step.help,
                'name': workflow_step.name,
                'type': workflow_step.type,
                'status': step_status.lower(),
                'link': create_link,
            }

            # Hook to allow subclasses to extend the step card attributes
            extended_card_options = self.extend_step_cards(
                workflow_step=workflow_step,
                step_status=step_status
            )

            card_dict.update(extended_card_options)
            steps.append(card_dict)

            previous_status = step_status

        # Get the current app
        active_app = get_active_app(request)

        context.update({
            'workflow': workflow,
            'steps': steps,
            'current_step': current_step,
            'previous_step': previous_step,
            'next_step': next_step,
            'url_map_name': '{}:{}_workflow_step'.format(active_app.namespace, workflow.type),
            'map_title': workflow.name,
            'map_subtitle': workflow.DISPLAY_TYPE_SINGULAR,
        })

        # Hook for extending the context
        additional_context = self.extend_context(
            request=request,
            session=session,
            context=context,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )
        context.update(additional_context)
        return context

    def set_feature_selection(self, map_view, enabled=True):
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

    @workflow_step_controller()
    def save_step_data(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
        """
        Handle GET requests with method get-attributes-form.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            workflow(ResourceWorkflow): the workflow.
            step(ResourceWorkflowStep): the step.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        previous_step, next_step = workflow.get_adjacent_steps(step)

        # Create for previous, next, and current steps
        previous_url = None
        active_app = get_active_app(request)
        step_url_name = '{}:{}_workflow_step'.format(active_app.namespace, workflow.type)
        current_url = reverse(step_url_name, args=(resource.id, workflow.id, str(step.id)))

        # Get Managers Hook
        model_db, _ = self.get_managers(
            request=request,
            resource=resource,
            *args, **kwargs
        )

        if next_step:
            next_url = reverse(step_url_name, args=(resource.id, workflow.id, str(next_step.id)))
        else:
            # Return to back_url if there is no next step
            next_url = back_url

        if previous_step:
            previous_url = reverse(step_url_name, args=(resource.id, workflow.id, str(previous_step.id)))

        # Hook for processing step data
        response = self.process_step_data(
            request=request,
            session=session,
            step=step,
            model_db=model_db,
            current_url=current_url,
            previous_url=previous_url,
            next_url=next_url
        )

        return response

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
        if not all([isinstance(current_step, valid_class) for valid_class in self.valid_step_classes]):
            raise TypeError('Invalid step type for view: {}. Must be one of {}.'.format(
                type(current_step),
                ', '.join([valid_class.__name__ for valid_class in self.valid_step_classes])
            ))

    def extend_step_cards(self, workflow_step, step_status):
        """
        Hook for extending step card attributes.

        Args:
            workflow_step(ResourceWorkflowStep): The current step for which a card is being created.
            step_status(str): Status of the workflow_step.

        Returns:
            dict: dictionary containing key-value attributes to add to the step card.
        """
        return {}

    def extend_context(self, request, session, context, current_step, previous_step, next_step):
        """
        Hook for extending the view context.

        Args:
           request(HttpRequest): The request.
           session(sqlalchemy.orm.Session): Session bound to the steps.
           context(dict): Context object for the map view template.
           current_step(ResourceWorkflowStep): The current step to be rendered.
           previous_step(ResourceWorkflowStep): The previous step.
           next_step(ResourceWorkflowStep): The next step.

        Returns:
            dict: key-value pairs to add to context.
        """
        return {}

    def process_step_data(self, request, session, step, model_db, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            step(ResourceWorkflowStep): The step to be updated.
            model_db(ModelDatabase): The model database associated with the resource.
            current_url(str): URL to step.
            previous_url(str): URL to the previous step.
            next_url(str): URL to the next step.

        Returns:
            HttpResponse: A Django response.

        Raises:
            ValueError: exceptions that occur due to user error, provide helpful message to help user solve issue.
            RuntimeError: exceptions that require developer attention.
        """  # noqa: E501
        if 'next-submit' in request.POST:
            response = redirect(next_url)
        else:
            response = redirect(previous_url)
        return response