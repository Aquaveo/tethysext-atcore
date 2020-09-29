"""
********************************************************************************
* Name: dataset_workflow_result_view.py
* Author: nswain
* Created On: June 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from collections import OrderedDict
from tethys_sdk.gizmos import DataTableView
from tethysext.atcore.models.resource_workflow_results import PlotWorkflowResult
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethys_sdk.permissions import has_permission
from tethys_sdk.gizmos import BokehView
from bokeh.plotting import figure
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from tethys_sdk.gizmos import PlotlyView

log = logging.getLogger(__name__)


class PlotWorkflowResultView(WorkflowResultsView):
    """
    Plot Result View Controller
    """
    template_name = 'atcore/resource_workflows/plot_workflow_results_view.html'
    valid_result_classes = [PlotWorkflowResult]

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
        base_context = super().get_context(
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

        # Get the result
        result = self.get_result(request=request, result_id=result_id, session=session)

        # Get datasets
        datasets = result.datasets

        # Get options
        options = result.options

        # Page title same as result name
        page_title = options.get('page_title', result.name)

        # Get can_export_datatable permission
        can_export_datatable = has_permission(request, 'can_export_datatable')

        for ds in datasets:
            # Check if the export options is there
            dom_attribute = ""
            if 'plot_lib' in ds.keys():
                if can_export_datatable:
                    if ds['plot_lib'] == 'bokeh':
                        data_source = ColumnDataSource(ds['dataset'])
                        plot = figure(height=500, width=800, title=ds['title'])
                        plot.line("x", "y", source=data_source)
                        plot_view = BokehView(plot, height="500px")
                    else:
                        df = ds['dataset']
                        import plotly.graph_objs as go
                        dict_key = [x for x in df.to_dict().keys()]
                        plot_view = PlotlyView([go.Scatter(x=[value for value in df.to_dict()[dict_key[0]].values()],
                                                           y=[value for value in df.to_dict()[dict_key[1]].values()]),
                                                go.Scatter(x=[10, 11], y=[1, 10])])

            data_table = DataTableView(
                column_names=ds['dataset'].columns,
                rows=[list(record.values()) for record in ds['dataset'].to_dict(orient='records', into=OrderedDict)],
                dom=dom_attribute,
                **options.get('data_table_kwargs', {})
            )
            ds.update({'data_table': data_table})


        base_context.update({
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'page_title': page_title,
            'datasets': datasets,
            'plot_view_input': plot_view,
        })

        return base_context
