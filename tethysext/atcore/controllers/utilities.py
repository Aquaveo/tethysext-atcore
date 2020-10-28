"""
********************************************************************************
* Name: utilities.py
* Author: glarsen, nswain
* Created On: December 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
import plotly.graph_objs as go
import pandas as pd

from tethys_sdk.gizmos import BokehView
from tethys_sdk.gizmos import PlotlyView
from tethysext.atcore.models.resource_workflow_steps import FormInputRWS


def get_style_for_status(status):
    """
    Return appropriate style for given status.

    Args:
        status(str): One of StatusMixin statuses.

    Returns:
        str: style for the given status.
    """
    from tethysext.atcore.mixins import StatusMixin

    if status in [StatusMixin.STATUS_COMPLETE, StatusMixin.STATUS_APPROVED, StatusMixin.STATUS_REVIEWED]:
        return 'success'

    elif status in [StatusMixin.STATUS_SUBMITTED, StatusMixin.STATUS_UNDER_REVIEW,
                    StatusMixin.STATUS_CHANGES_REQUESTED, StatusMixin.STATUS_WORKING]:
        return 'warning'

    elif status in [StatusMixin.STATUS_ERROR, StatusMixin.STATUS_FAILED, StatusMixin.STATUS_REJECTED]:
        return 'danger'

    return 'primary'


def get_plot_object_from_result(result):
    # Get datasets.
    datasets = result.datasets

    # Get plot object
    plot_object = result.plot

    # Get options.
    options = result.options

    # Page title same as result name.
    # page_title = options.get('page_title', result.name)

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
                                              legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02,
                                                      'xanchor': 'right', 'x': 1},
                                              margin={'r': 0},
                                              height=600))

        # Plot count variable to keep track of the series color in bokeh.
        plot_count = 0

        # label count variable to keep track of default variable number.
        label_count = 1
        for ds in datasets:
            series_axes = [('x', 'y')]
            # series_labels is for panda frame with multiple columns representing multiple series.
            series_labels = ''
            if 'title' in ds.keys():
                series_label = ds['title']

            # Handle panda dataframe with multiple columns. If panda dataframe has multiple columns and has no
            # series_axes, we'll assume the first one is x and the rest are ys.
            if 'series_axes' in ds.keys():
                series_axes = ds['series_axes']
                if not series_axes:
                    column_names = ds['dataset'].columns.to_list()
                    for col in column_names[1:]:
                        # Assume 1st column is x and the rest is y
                        series_axes.append((column_names[0], col))

            # Create default series label for panda dataframe with multiple columns.
            if 'series_labels' in ds.keys():
                series_labels = ds['series_labels']
                if not series_labels:
                    for i in range(len(series_axes)):
                        series_labels.append(f"Data Series {label_count}")
                        label_count += 1
            if 'dataset' in ds.keys():
                if series_axes:
                    plot_data = ds['dataset']
                    if renderer == 'bokeh':
                        for i, axis in enumerate(series_axes):
                            if isinstance(plot_data, pd.DataFrame):
                                x_axis = axis[0] if axis[0] == plot_data.columns[0] else plot_data.columns[0]
                                y_axis = axis[1] if axis[1] == plot_data.columns[1] else plot_data.columns[1]
                                data = {'x': plot_data[x_axis].to_list(), 'y': plot_data[y_axis].to_list()}

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
                        for i, axis in enumerate(series_axes):
                            # Handle panda dataframe with multiple columns
                            if isinstance(series_labels, list):
                                series_label = series_labels[i]
                            if isinstance(plot_data, pd.DataFrame):
                                x_axis = axis[0] if axis[0] == plot_data.columns[0] else plot_data.columns[0]
                                y_axis = axis[1] if axis[1] == plot_data.columns[1] else plot_data.columns[1]
                                plot.add_trace(go.Scatter(x=plot_data[x_axis].to_list(),
                                                          y=plot_data[y_axis].to_list(), name=series_label,
                                                          mode=plot_mode, line_shape=line_shape))
                            else:
                                plot.add_trace(go.Scatter(x=plot_data[0], y=plot_data[1], name=series_label,
                                                          mode=plot_mode, line_shape=line_shape))

        # Plot the chart.
        if renderer == 'bokeh':
            plot_view = BokehView(plot, height='95%', width='95%')
        elif renderer == 'plotly':
            plot_view = PlotlyView(plot, height='95%', width='95%')

    return plot_view


def get_tabular_data_for_previous_steps(current_step):
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