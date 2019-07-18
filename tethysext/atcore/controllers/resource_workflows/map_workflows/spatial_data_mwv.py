"""
********************************************************************************
* Name: spatial_data_mwv.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialDatasetRWS, SpatialAttributesRWS
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_controller


class SpatialDataMWV(MapWorkflowView):
    """
    Abstract controller for a map workflow view data assigned to each feature.
    """
    template_name = 'atcore/resource_workflows/spatial_data_mwv.html'
    valid_step_classes = [SpatialDatasetRWS, SpatialAttributesRWS]

    # Disable the properties popup so we can create a custom pop-up
    properties_popup_enabled = False

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
        if not current_step.options['geometry_source']:
            raise RuntimeError('The geometry option is required.')

        # Get geometry from option
        geometry = current_step.to_geojson()

        # Turn off feature selection
        map_view = context['map_view']
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Get managers
        _, map_manager = self.get_managers(
            request=request,
            resource=resource
        )

        geometry_layer = map_manager.build_geojson_layer(
            geojson=geometry,
            layer_name='_pop_up_features',
            layer_variable='pop_up_features',
            layer_title='Pop Up Features',
            popup_title=current_step.options['dataset_title'],
            selectable=True
        )

        map_view.layers.insert(0, geometry_layer)

        # Disable the default properties popup for users that can edit
        has_active_role = self.user_has_active_role(request, current_step)
        if has_active_role:
            enable_properties = False
        else:
            enable_properties = True

        # Save changes to map view
        context.update({
            'map_view': map_view,
            'enable_properties_popup': enable_properties,
            'enable_spatial_data_popup': not enable_properties
        })

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
        pass

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
        pass
