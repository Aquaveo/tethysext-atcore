"""
********************************************************************************
* Name: set_status_wv.py
* Author: nswain
* Created On: August 19, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging

from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SetStatusRWS

log = logging.getLogger(__name__)


class SetStatusWV(ResourceWorkflowView):
    """
    Controller for SetStatusRWS.
    """
    template_name = 'atcore/resource_workflows/set_status_wv.html'
    valid_step_classes = [SetStatusRWS]
    default_status_label = 'Status'

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
        # Validate the statuses option
        current_step.validate_statuses()

        # Status style
        status = current_step.get_status(current_step.ROOT_STATUS_KEY)
        status_style = self.get_style_for_status(status)

        # Save changes to map view and layer groups
        context.update({
            'read_only': not self.user_has_active_role(request, current_step),
            'form_title': current_step.options.get('form_title', current_step.name),
            'status_label': current_step.options.get('status_label', self.default_status_label),
            'statuses': current_step.options.get('statuses', []),
            'comments': current_step.get_parameter('comments'),
            'status': status,
            'status_style': status_style
        })

    def process_step_data(self, request, session, step, model_db, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs. Only called if the user has an active role.

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
        status = request.POST.get('status', None)
        comments = request.POST.get('comments', '')

        if not status:
            raise ValueError(f'The "{step.options.get("status_label", self.default_status_label)}" field '
                             f'is required.')

        if status not in step.valid_statuses():
            raise RuntimeError(f'Invalid status given: "{status}"')

        # Save parameters
        step.set_parameter('comments', comments)
        session.commit()

        # Validate the parameters
        step.validate()

        # Set the status
        step.set_status(step.ROOT_STATUS_KEY, status)
        step.set_attribute(step.ATTR_STATUS_MESSAGE, None)
        session.commit()

        response = super().process_step_data(
            request=request,
            session=session,
            step=step,
            model_db=model_db,
            current_url=current_url,
            previous_url=previous_url,
            next_url=next_url
        )

        return response
