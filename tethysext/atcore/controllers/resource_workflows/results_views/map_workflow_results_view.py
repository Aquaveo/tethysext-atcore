"""
********************************************************************************
* Name: map_workflow_results_view.py
* Author: nswain
* Created On: October 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import logging
from django.http import JsonResponse
import json

from tethys_sdk.gizmos import SelectInput
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView


log = logging.getLogger(__name__)


class MapWorkflowResultsView(MapWorkflowView, WorkflowResultsView):
    """
    Map Result View controller.
    """
    template_name = 'atcore/resource_workflows/map_workflow_results_view.html'
    valid_result_classes = [SpatialWorkflowResult]
    show_legends = True

    def get_context(self, request, session, resource, context, model_db, workflow_id, step_id, result_id, *args,
                    **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        base_context = MapWorkflowView.get_context(
            self,
            request=request,
            session=session,
            resource=resource,
            context=context,
            model_db=model_db,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        result_workflow_context = WorkflowResultsView.get_context(
            self,
            request=request,
            session=session,
            resource=resource,
            context=context,
            model_db=model_db,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id,
            *args, **kwargs
        )

        # Combine contexts
        base_context.update(result_workflow_context)

        # Add layers from geometry in data
        map_view = base_context['map_view']

        # Turn off feature selection on current layers
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Get the result object for this view
        result = self.get_result(request, result_id, session)
        # Get managers
        _, map_manager = self.get_managers(
            request=request,
            resource=resource,
            *args, **kwargs
        )

        # Get Map View and Layer Groups
        layer_groups = base_context['layer_groups']
        # Generate MVLayers for spatial data
        results_layers = []
        legends_select_input = []
        legends = []
        # Build MVLayers for map
        for layer in result.layers:
            layer_type = layer.pop('type', None)

            if not layer_type or layer_type not in ['geojson', 'wms']:
                log.warning('Unsupported layer type will be skipped: {}'.format(layer))
                continue

            result_layer = None

            if layer_type == 'geojson':
                result_layer = map_manager.build_geojson_layer(**layer)

            elif layer_type == 'wms':
                result_layer = map_manager.build_wms_layer(**layer)

            # build legend:
            legend = map_manager.build_legend(layer, units=result.options.get('units', ''))
            legend_input_options = [(color_ramp, color_ramp) for color_ramp in legend['color_list']]
            legend_attrs = {"onchange": f"ATCORE_MAP_VIEW.reload_legend(this, {legend['min_value']}, "
                                        f"{legend['max_value']}, '{legend['layer_id']}' )"}

            legend_select_input = SelectInput(name=f"tethys-color-ramp-picker-{legend['legend_id']}",
                                              options=legend_input_options,
                                              initial=[legend['color_ramp']],
                                              attributes=legend_attrs)

            legends_select_input.append(legend_select_input)
            legends.append(legend)

            if result_layer:
                # Add layer to beginning the map's of layer list
                map_view.layers.insert(0, result_layer)
                results_layers.append(result_layer)

        # Build the Layer Group for Workflow Layers
        if results_layers:
            results_layer_group = map_manager.build_layer_group(
                id='workflow_results',
                display_name=result.options.get('layer_group_title', 'Results'),
                layer_control=result.options.get('layer_group_control', 'checkbox'),
                layers=results_layers
            )

            layer_groups.insert(0, results_layer_group)

        base_context.update({
            'legends': zip(legends, legends_select_input),
            'show_legends': self.show_legends,
        })
        return base_context

    def get_plot_data(self, request, session, resource, result_id, *args, **kwargs):
        """
        Load plot from given parameters.

        Args:
            request (HttpRequest): The request.
            session(sqlalchemy.Session): The database session.
            resource(Resource): The resource.

        Returns:
            JsonResponse: title, data, and layout options for the plot.
        """
        # Get Resource
        layer_name = request.POST.get('layer_name', '')
        layer_id = request.POST.get('layer_id', layer_name)
        feature_id = request.POST.get('feature_id', '')

        result = self.get_result(request, result_id, session)

        layer = result.get_layer(layer_id)

        layer_type = layer.get('type', None)

        if not layer_type or layer_type not in ['geojson', 'wms']:
            raise TypeError('Unsupported layer type: {}'.format(layer))

        if layer_type == 'geojson':
            title, data, layout = self.get_plot_for_geojson(layer, feature_id)

        elif layer_type == 'wms':
            title, data, layout = super().get_plot_data(request, session, resource)

        return JsonResponse({'title': title, 'data': data, 'layout': layout})

    def get_plot_for_geojson(self, layer, feature_id):
        """
        Retrieves plot for feature from given layer.

        Args:
            layer(dict): layer dictionary.
            feature_id(str): id of the feature in the layer to plot.

        Returns:
            title, data, layout: Plot dictionary.
        """
        plot = None
        try:
            # Example layer:
            # {
            #     'type': 'geojson',
            #     'geojson':
            #         {
            #             'type': 'FeatureCollection',
            #             'crs': {...},
            #             'features': [...]
            #         },
            #     'layer_name': 'detention_basin_boundaries',
            #     'layer_variable': 'detention_basin_boundaries',
            #     'layer_title': 'Detention Basins',
            #     'popup_title': 'Detention Basin',
            #     'selectable': False
            # }
            for feature in layer['geojson']['features']:
                # Example of a feature:
                # {
                #     'type': 'Feature',
                #     'geometry': {'type': 'Point', 'coordinates': [-87.87625096273638, 30.65151178301437]},
                #     'properties': {
                #         'id': 1,
                #         'plot': {
                #             'title': 'Plot 1',
                #             'data': [
                #                 {
                #                     'name': 'Foo',
                #                     'x': [2, 4, 6, 8],
                #                     'y': [10, 15, 20, 25]
                #                 },
                #                 {
                #                     'name': 'Bar',
                #                     'x': [1, 3, 5, 9],
                #                     'y': [9, 6, 12, 15]
                #                 },
                #             ],
                #         }
                #     }
                # }
                if str(feature['properties']['id']) == str(feature_id):
                    plot = feature['properties'].get('plot', None)
                    break

        except KeyError:
            log.warning('Ill formed geojson: {}'.format(layer))

        title = plot.get('title', '') if plot else None
        data = plot.get('data', []) if plot else None
        layout = plot.get('layout', {}) if plot else None

        return title, data, layout

    def update_result_layer(self, request, session, resource, *args, **kwargs):
        # Get Managers Hook
        model_db, map_manager = self.get_managers(
            request=request,
            resource=resource,
            *args, **kwargs
        )
        result = self.get_result(request, kwargs['result_id'], session)
        layer_id = json.loads(request.POST.get('layer_id'))
        color_ramp = json.loads(request.POST.get('color_ramp'))

        result.update_layer(layer_id=layer_id, color_ramp=color_ramp)

        return JsonResponse({'success': True})
