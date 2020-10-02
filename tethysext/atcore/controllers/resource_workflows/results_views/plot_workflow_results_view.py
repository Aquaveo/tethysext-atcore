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

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
import plotly.graph_objs as go
from datetime import datetime

from tethys_sdk.gizmos import BokehView
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

        # Get plot lib
        plot_lib = options.get('plot_lib', 'plotly')

        # Get axes option
        plot_axes = options.get('axes', [])

        # Get labels option
        plot_labels = options.get('labels', [])

        # Set plot options
        plot_type = options.get('plot_type', 'lines')

        # Set plot options
        axis_labels = options.get('axis_labels', ['x', 'y'])

        # Set line shape
        line_shape = options.get('line_shape', 'linear')

        plot_view = None
        for ds in datasets:
            if 'dataset' in ds.keys():
                df = ds['dataset']

                # Build plot_axes list if it's not defined
                if not plot_axes:
                    column_names = df.columns.to_list()
                    for count, col in enumerate(column_names[1:], 1):
                        # Assume 1st column is x and the rest is y
                        plot_axes.append((column_names[0], col))

                if not plot_labels:
                    for i, _ in enumerate(plot_axes, 1):
                        plot_labels.append(f"Data Series {str(i)}")

                if plot_lib == 'bokeh':
                    x_axis_type = 'linear'
                    # if the first item in the x axis is datetime, the x_axis_type is datetime.
                    if isinstance(df[plot_axes[0][0]][0], datetime):
                        x_axis_type = 'datetime'
                    plot = figure(x_axis_type=x_axis_type)
                    plot.xaxis.axis_label = axis_labels[0]
                    plot.yaxis.axis_label = axis_labels[1]
                    for i, axis in enumerate(plot_axes):
                        data = {'x': df[axis[0]].to_list(), 'y': df[axis[1]].to_list()}
                        if plot_type == 'lines':
                            plot.line("x", "y", source=ColumnDataSource(data), legend_label=plot_labels[i],
                                      color=Category10[10][i % 10])
                        else:
                            plot.scatter("x", "y", source=ColumnDataSource(data), legend_label=plot_labels[i],
                                         color=Category10[10][i % 10])
                    plot_view = BokehView(plot, height='95%', width='95%')
                else:
                    plot = go.Figure(layout=go.Layout(xaxis={'title': {'text': axis_labels[0]}},
                                                      yaxis={'title': {'text': axis_labels[1]}},
                                                      height=600))
                    plot_mode = 'lines' if plot_type == 'lines' else 'markers'
                    for i, axis in enumerate(plot_axes):
                        plot.add_trace(go.Scatter(x=df[axis[0]].to_list(), y=df[axis[1]].to_list(), name=plot_labels[i],
                                                  mode=plot_mode, line_shape=line_shape))

                    plot_view = PlotlyView(plot, height='95%', width='95%')

            elif 'plot_object' in ds.keys():
                plot = ds['plot_object']
                # Only support Plotly for now because we can't serialize bokeh plot.
                plot_view = PlotlyView(plot, height='95%', width='95%')

        base_context.update({
            'page_title': page_title,
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'datasets': datasets,
            'plot_view_input': plot_view,
        })

        return base_context
