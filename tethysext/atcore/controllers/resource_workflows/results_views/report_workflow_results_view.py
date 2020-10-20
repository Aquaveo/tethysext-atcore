"""
********************************************************************************
* Name: report_workflow_results_view.py
* Author: nswain, htran, msouffront
* Created On: October 14, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
from django.http import JsonResponse
from tethysext.atcore.models.resource_workflow_results import ReportWorkflowResult
from tethysext.atcore.models.resource_workflow_steps import FormInputRWS
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethysext.atcore.models.resource_workflow_results import DatasetWorkflowResult, PlotWorkflowResult,\
    SpatialWorkflowResult
from tethysext.atcore.controllers.utiltities import get_plot_object_from_result

from tethys_sdk.gizmos import DataTableView, MapView
from collections import OrderedDict


log = logging.getLogger(__name__)


class ReportWorkflowResultsView(MapWorkflowView, WorkflowResultsView):
    """
    Report Result View controller.
    """
    template_name = 'atcore/resource_workflows/report_workflow_results_view.html'
    valid_result_classes = [ReportWorkflowResult]

    previous_steps_selectable = True

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
        # Turn off feature selection on model layers
        map_view = context['map_view']
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Can run workflows if not readonly
        can_run_workflows = not self.is_read_only(request, current_step)

        # get tabular data if any
        tabular_data = self.get_tabular_data_for_previous_steps(
            current_step=current_step,
        )
        has_tabular_data = len(tabular_data) > 0

        # Generate MVLayers for spatial data
        # Get managers
        _, map_manager = self.get_managers(
            request=request,
            resource=resource,
        )

        # Get DatasetWorkflowResult
        results = list()
        for result in current_step.results:
            if isinstance(result, DatasetWorkflowResult):
                for ds in result.datasets:
                    # Check if the export options is there
                    data_table = DataTableView(
                        column_names=ds['dataset'].columns,
                        rows=[list(record.values()) for record in ds['dataset'].to_dict(orient='records',
                                                                                        into=OrderedDict)],
                        searching=False,
                        paging=False,
                        info=False
                    )
                    ds.update({'data_table': data_table})
                    results.append({'dataset': ds})
            elif isinstance(result, PlotWorkflowResult):
                results.append({'plot': [result.name, get_plot_object_from_result(result)]})
            elif isinstance(result, SpatialWorkflowResult):
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

                    if result_layer:
                        result_layer.options['url'] = self.geoserver_url(result_layer.options['url'])
                        # Add layer to beginning the map's of layer list
                        map_view.layers.insert(0, result_layer)

                        # Append to final results list.
                        results.append({'map': result_layer})
        # Save changes to map view and layer groups
        context.update({
            'can_run_workflows': can_run_workflows,
            'has_tabular_data': has_tabular_data,
            'tabular_data': tabular_data,
            'report_results': results,
        })
        # Note: new layer created by super().process_step_options will have feature selection enabled by default
        super().process_step_options(
            request=request,
            session=session,
            context=context,
            resource=resource,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )

    def get_tabular_data_for_previous_steps(self, current_step):
        previous_steps = current_step.workflow.get_previous_steps(current_step)
        steps_to_skip = set()
        mappable_tabular_step_types = (FormInputRWS,)
        step_data = {}
        for step in previous_steps:
            # skip non form steps
            if step in steps_to_skip or not isinstance(step, mappable_tabular_step_types):
                continue

            step_params = step.get_parameter('form-values')
            fixed_params = {x.replace('_', ' ').title(): step_params[x] for x in step_params}
            step_data[step.name] = fixed_params

        return step_data

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

    @staticmethod
    def geoserver_url(link):
        """
        link: 'http://admin:geoserver@192.168.99.163:8181/geoserver/wms/'
        :return: 'http://192.168.99.163:8181/geoserver/wms/'
        """
        start_remove_index = link.find('//') + 2
        end_remove_index = link.find('@') + 1
        link = link[:start_remove_index] + link[end_remove_index:]
        return link
