"""
********************************************************************************
* Name: form_input_wv.py
* Author: mmlebaron, glarsen
* Created On: October 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.resource_workflow_steps.form_input_rws import FormInputRWS
from tethysext.atcore.forms.widgets.param_widgets import generate_django_form

log = logging.getLogger(__name__)


class FormInputWV(ResourceWorkflowView):
    """
    Controller for FormInputRWV.
    """
    template_name = 'atcore/resource_workflows/form_input_wv.html'
    valid_step_classes = [FormInputRWS]

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
        # Status style
        form_title = current_step.options.get('form_title', current_step.name) or current_step.name

        p = current_step.options['param_class']
        form = generate_django_form(p, form_field_prefix='param-form-')

        # Save changes to map view and layer groups
        context.update({
            'read_only': self.is_read_only(request, current_step),
            'form_title': form_title,
            'form': form,
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
        """  # noqa: E501
        params = {}
        for p in request.POST:
            if p.startswith('param-form-'):
                param_name = p[11:]
                params[param_name] = request.POST.get(p, None)
        step.set_parameter('form-values', params)

        status = step.STATUS_COMPLETE

        # Save parameters
        session.commit()

        # Validate the parameters
        step.validate()

        # Set the status
        step.set_status(status=status)
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
