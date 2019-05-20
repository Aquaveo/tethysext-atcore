"""
********************************************************************************
* Name: spatial_data_mwv.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethys_sdk.gizmos import MVLayer
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
        geometry = current_step.resolve_option('geometry_source')

        # Turn off feature selection
        map_view = context['map_view']
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Create new layer for geometry
        geometry_layer = MVLayer(
            source='GeoJSON',
            options=geometry,
            legend_title='_pop_up_features',
            layer_options={
                # 'style': {
                #     'fill': {
                #         'color': 'rbga(255,0,0,0.5)'
                #     },
                #     'stroke': {
                #         'color': 'rbga(0,255,0,1.0)',
                #         'width': 3
                #     }
                # },
            },
            feature_selection=True,
            editable=False,
            data={}
        )

        map_view.layers.insert(0, geometry_layer)

        # Save changes to map view
        context.update({
            'map_view': map_view,
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
