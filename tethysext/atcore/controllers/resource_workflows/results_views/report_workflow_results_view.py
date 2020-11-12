"""
********************************************************************************
* Name: report_workflow_results_view.py
* Author: nswain, htran, msouffront
* Created On: October 14, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
from tethysext.atcore.models.resource_workflow_results import ReportWorkflowResult
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethysext.atcore.models.resource_workflow_results import DatasetWorkflowResult, PlotWorkflowResult, \
    SpatialWorkflowResult

from tethys_sdk.gizmos import DataTableView
from tethys_sdk.gizmos import BokehView
from tethys_sdk.gizmos import PlotlyView
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
        tabular_data = current_step.workflow.get_tabular_data_for_previous_steps(current_step)
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
                    ds.update({'data_description': result.description})
                    results.append({'dataset': ds})
            elif isinstance(result, PlotWorkflowResult):
                renderer = result.options.get('renderer', 'plotly')
                plot_view_params = dict(plot_input=result.get_plot_object(), height='95%', width='95%')
                plot_view = BokehView(**plot_view_params) if renderer == 'bokeh' else PlotlyView(**plot_view_params)
                results.append({'plot': {'name': result.name, 'description': result.description, 'plot': plot_view}})
            elif isinstance(result, SpatialWorkflowResult):
                # Get layer params
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
                        # Update env param
                        params = ""
                        if 'params' in result_layer['options'].keys():
                            params = result_layer['options']['params']
                        if params:
                            if 'TILED' in params.keys():
                                params.pop('TILED')
                            if 'TILESORIGIN' in params.keys():
                                params.pop('TILESORIGIN')
                        result_layer['options']['params'] = params

                        # Build Legend
                        legend_info = map_manager.build_legend(layer, units=result.options.get('units', ''))

                        result_layer.options['url'] = self.geoserver_url(result_layer.options['url'])
                        # Add layer to beginning the map's of layer list
                        # map_view.layers.insert(0, result_layer)
                        # Append to final results list.
                        results.append({'map': {'name': result.name, 'description': result.description,
                                                'legend': legend_info, 'map': result_layer}})

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

        return base_context

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
