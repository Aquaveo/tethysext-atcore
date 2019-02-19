"""
********************************************************************************
* Name: spatial_input_mwv
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import param
from tethys_sdk.gizmos import MVLayer
from tethysext.atcore import widgets
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.app_users.resource_workflow_steps import SpatialAttributesRWS


class SpatialAttributesMWV(MapWorkflowView):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_attributes_mwv.html'

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
        if not current_step.options['geometry']:
            raise RuntimeError('The geometry option is required.')

        if not current_step.options['attributes']:
            raise RuntimeError('The attributes option is required.')

        # Get geometry
        geometry = None
        geometry_opts = current_step.options['geometry']

        if isinstance(geometry_opts, dict) and current_step.OPT_PARENT_STEP in geometry_opts:
            field_name = geometry_opts[current_step.OPT_PARENT_STEP]
            parent_step = current_step.parent

            try:
                geometry = parent_step.get_parameter(field_name)
            except ValueError as e:
                raise RuntimeError(str(e))

        # Create spatial form
        SpatialAttributesParam = type(
            'SpatialAttributesParam',
            (param.Parameterized,),
            current_step.options['attributes']
        )

        spatial_attributes_param = SpatialAttributesParam()
        dynamic_form = widgets.widgets(spatial_attributes_param, {})
        print(dynamic_form)  # TODO: USE THIS

        # Turn off feature selection
        map_view = context['map_view']
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Create new layer for geometry
        geometry_layer = MVLayer(
            source='GeoJSON',
            options=geometry,
            legend_title='Test GeoJSON',
            layer_options={
                'style': {
                    'fill': {
                        'color': 'rbga(255,0,0,0.5)'
                    },
                    'stroke': {
                        'color': 'rbga(0,255,0,1.0)',
                        'width': 3
                    }
                },
            },
            feature_selection=True,
            editable=False,
            data={}
        )

        map_view.layers.insert(0, geometry_layer)

        # Save changes to map view
        context.update({'map_view': map_view})
