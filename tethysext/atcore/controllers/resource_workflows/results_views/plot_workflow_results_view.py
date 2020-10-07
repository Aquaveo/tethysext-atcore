"""
********************************************************************************
* Name: plot_workflow_result_view.py
* Author: nathan, htran, msouff
* Created On: Oct 7, 2020
* Copyright: (c) Aquaveo 2020
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
import pandas as pd
import numpy as np

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

        # Get datasets.
        datasets = result.datasets

        # Get plot object
        plot_object = result.plot

        # Get options.
        options = result.options

        # Page title same as result name.
        page_title = options.get('page_title', result.name)

        # Get renderer.
        renderer = options.get('renderer', 'plotly')

        # Set plot options.
        plot_type = options.get('plot_type', 'lines')

        # Set plot options.
        axis_labels = options.get('axis_labels', ['x', 'y'])

        # Set line shape.
        line_shape = options.get('line_shape', 'linear')

        # X axis type.
        x_axis_type = options.get('x_axis_type', 'linear')

        # Initial plot is None.
        plot_view = None

        # Handle the case where the user just provide a plotly object.
        if isinstance(plot_object, dict):
            if 'plot_object' in plot_object.keys():
                # Only support Plotly for now because we can't serialize bokeh plot.
                plot_view = PlotlyView(plot_object['plot_object'], height='95%', width='95%')
        else:
            # Set layout such as axis label for x and y axis.
            if renderer == 'bokeh':
                plot = figure(x_axis_type=x_axis_type, plot_width=900)
                plot.xaxis.axis_label = axis_labels[0]
                plot.yaxis.axis_label = axis_labels[1]
            elif renderer == 'plotly':
                plot = go.Figure(layout=go.Layout(xaxis={'title': {'text': axis_labels[0]}},
                                                  yaxis={'title': {'text': axis_labels[1]}},
                                                  height=600))

            # Plot count variable to keep track of the series color in bokeh.
            plot_count = 0

            # label count variable to keep track of default variable number.
            label_count = 1
            for ds in datasets:
                plot_axes = [('x', 'y')]
                # series_labels is for panda frame with multiple columns representing multiple series.
                series_labels = ''
                if 'title' in ds.keys():
                    series_label = ds['title']

                # Handle panda dataframe with multiple columns. If panda dataframe has multiple columns and has no
                # plot_axes, we'll assume the first one is x and the rest are y.
                if 'plot_axes' in ds.keys():
                    plot_axes = ds['plot_axes']
                    if not plot_axes:
                        column_names = ds['dataset'].columns.to_list()
                        for col in column_names[1:]:
                            # Assume 1st column is x and the rest is y
                            plot_axes.append((column_names[0], col))

                # Create default series label for panda dataframe with multiple columns.
                if 'series_labels' in ds.keys():
                    series_labels = ds['series_labels']
                    if not series_labels:
                        for i in range(len(plot_axes)):
                            series_labels.append(f"Data Series {label_count}")
                            label_count += 1
                if 'dataset' in ds.keys():
                    if plot_axes:
                        plot_data = ds['dataset']
                        if renderer == 'bokeh':
                            for i, axis in enumerate(plot_axes):
                                if isinstance(plot_data, pd.DataFrame):
                                    try:
                                        data = {'x': plot_data[axis[0]].to_list(), 'y': plot_data[axis[1]].to_list()}
                                    except KeyError:
                                        data = {'x': plot_data[plot_data.columns[0]].to_list(),
                                                'y': plot_data[plot_data.columns[1]].to_list()}
                                elif isinstance(plot_data, list):
                                    data = {'x': plot_data[0], 'y': plot_data[1]}

                                # Handle panda dataframe with multiple columns
                                if isinstance(series_labels, list):
                                    series_label = series_labels[i]

                                if plot_type == 'lines':
                                    plot.line("x", "y", source=ColumnDataSource(data), legend_label=series_label,
                                              color=Category10[10][plot_count % 10])
                                    plot_count += 1
                                else:
                                    plot.scatter("x", "y", source=ColumnDataSource(data), legend_label=series_label,
                                                 color=Category10[10][plot_count % 10])
                                    plot_count += 1
                        else:
                            plot_mode = 'lines' if plot_type == 'lines' else 'markers'
                            for i, axis in enumerate(plot_axes):
                                # Handle panda dataframe with multiple columns
                                if isinstance(series_labels, list):
                                    series_label = series_labels[i]
                                if isinstance(plot_data, pd.DataFrame):
                                    try:
                                        plot.add_trace(go.Scatter(x=plot_data[axis[0]].to_list(),
                                                                  y=plot_data[axis[1]].to_list(), name=series_label,
                                                                  mode=plot_mode, line_shape=line_shape))
                                    except KeyError:
                                        plot.add_trace(go.Scatter(x=plot_data[plot_data.columns[0]].to_list(),
                                                                  y=plot_data[plot_data.columns[1]].to_list(),
                                                                  name=series_label, mode=plot_mode,
                                                                  line_shape=line_shape))
                                else:
                                    plot.add_trace(go.Scatter(x=plot_data[0], y=plot_data[1], name=series_label,
                                                              mode=plot_mode, line_shape=line_shape))

            # Plot the chart.
            if renderer == 'bokeh':
                plot_view = BokehView(plot, height='95%', width='95%')
            elif renderer == 'plotly':
                plot_view = PlotlyView(plot, height='95%', width='95%')

        base_context.update({
            'page_title': page_title,
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'datasets': datasets,
            'plot_view_input': plot_view,
        })

        return base_context
