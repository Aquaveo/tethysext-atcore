"""
********************************************************************************
* Name: dataset_workflow_result_view.py
* Author: nswain
* Created On: June 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from tethysext.atcore.models.resource_workflow_results import PlotWorkflowResult
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethys_sdk.gizmos import BokehView
from tethys_sdk.gizmos import PlotlyView

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
import plotly.graph_objs as go


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

        # Get plot lib
        plot_lib = options.get('plot_lib', 'bokeh')

        # Get axes option
        # axes(list): A list of tuples for pair axis ex: ([('x', 'y'), ('x1', 'y1'), ('x', 'y2')])
        plot_axes = options.get('axes', [])

        # Get labels option
        # labels(list): Label for each series
        plot_labels = options.get('labels', [])

        # Set plot options
        plot_type = options.get('plot_type', 'lines')

        for ds in datasets:
            df = ds['dataset']

            # Build plot_axes list if it's not defined
            if not plot_axes:
                column_names = df.columns.to_list()
                for count, col in enumerate(column_names[1:], 1):
                    # Assume 1st column is x and the rest is y
                    plot_axes.append((column_names[0], col))

            if not plot_labels:
                for i, _ in enumerate(plot_axes, 1):
                    plot_labels.append(f"Data Series {i}")

            if plot_lib == 'bokeh':
                plot = figure(title=ds['title'])

                for i, axis in enumerate(plot_axes):
                    data = {'x': df[axis[0]].to_list(), 'y': df[axis[1]].to_list()}
                    if plot_type == 'lines':
                        plot.line("x", "y", source=ColumnDataSource(data), legend_label=plot_labels[i],
                                  color=Category10[10][i % 10])
                    else:
                        plot.scatter("x", "y", source=ColumnDataSource(data), legend_label=plot_labels[i],
                                     color=Category10[10][i % 10])
                plot_view = BokehView(plot)
            else:
                plot = go.Figure(layout=go.Layout(title=ds['title']))
                plot_mode = 'lines' if plot_type == 'lines' else 'markers'
                for i, axis in enumerate(plot_axes):
                    plot.add_trace(go.Scatter(x=df[axis[0]].to_list(), y=df[axis[1]].to_list(), name=plot_labels[i],
                                              mode=plot_mode))

                plot_view = PlotlyView(plot)

        base_context.update({
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'datasets': datasets,
            'plot_view_input': plot_view,
        })

        return base_context
