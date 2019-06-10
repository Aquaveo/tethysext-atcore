"""
********************************************************************************
* Name: spatial_attributes_mwv.py
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import param
from django.shortcuts import render
from django.http import JsonResponse
from tethysext.atcore.forms.widgets.param_widgets import generate_django_form
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_data_mwv import SpatialDataMWV
from tethysext.atcore.models.resource_workflow_steps import SpatialAttributesRWS
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_controller


class SpatialAttributesMWV(SpatialDataMWV):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    valid_step_classes = [SpatialAttributesRWS]

    @staticmethod
    def get_params(current_step):
        """
        Get the an instance of the Paramaterized object containing the attribute definitions.

        Args:
            current_step(ResourceWorkflowStep): The current step instance.

        Returns:
            Parameterized: Instance of a Parameterized object with Parameters for each attribute.
        """
        # Add hidden id field
        attribute_fields = current_step.options['attributes']

        # Create spatial form
        SpatialAttributesParam = type(
            'SpatialAttributesParam',
            (param.Parameterized,),
            attribute_fields
        )

        # Generate Django form from params
        params = SpatialAttributesParam()
        return params

    @workflow_step_controller(is_rest_controller=True)
    def get_popup_form(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
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
        # GET Parameters
        feature_id = int(request.GET.get('feature-id', 0))

        sa_params = self.get_params(step)
        attributes_form = generate_django_form(sa_params, {})

        context = {
            'attributes_form': attributes_form,
            'feature_id': feature_id
        }

        return render(request, 'atcore/resource_workflows/components/spatial_attributes_form.html', context)

    @workflow_step_controller(is_rest_controller=True)
    def save_spatial_data(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
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
        print(request.POST)
        print(request.GET)
        return JsonResponse({'success': True})
