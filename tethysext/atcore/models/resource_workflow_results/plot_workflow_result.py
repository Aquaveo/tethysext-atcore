"""
********************************************************************************
* Name: plot_workflow_result.py
* Author: nathan, htran, msouff
* Created On: Oct 7, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import copy
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10
import plotly.graph_objs as go

from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult

__all__ = ['PlotWorkflowResult']


class PlotWorkflowResult(ResourceWorkflowResult):
    """
    Data model for storing spatial information about resource workflow results.

    Options:
        renderer (str): bokeh or plotly
        axes(list): A list of tuples for pair axis ex. For example: [('x', 'y'), ('x1', 'y1'), ('x', 'y2')]
        axis_labels(list): A list of label for x and y axes respectively. For example: ['x', 'y']
        plot_type (str): lines, scatter, or bar
        line_shape (str): Only for plotly. You can select from on of these options: linear, spline, vhv, hvh, vh, hv
        x_axis_type (str): type of x axis. Available options are 'linear' or 'datetime'
    """
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView'  # noqa: E501
    TYPE = 'plot_workflow_result'

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        Args:
        """
        super().__init__(*args, **kwargs)

    @property
    def default_options(self):
        """
        Returns default options dictionary for the object.
        """

        default_options = super().default_options
        default_options.update({
            'renderer': 'plotly',
            'axes': [],
            'plot_type': 'lines',
            'axis_labels': ['x', 'y'],
            'line_shape': 'linear',
            'x_axis_type': 'datetime',
            'no_dataset_message': 'No dataset found.'
        })
        return default_options

    @property
    def datasets(self):
        if 'datasets' not in self.data:
            self.data['datasets'] = []
        return copy.deepcopy(self.data['datasets'])

    @datasets.setter
    def datasets(self, value):
        data = copy.deepcopy(self.data)
        data['datasets'] = value
        self.data = data

    @property
    def plot(self):
        if 'plot' not in self.data:
            self.data['plot'] = ''
        return copy.deepcopy(self.data['plot'])

    @plot.setter
    def plot(self, value):
        data = copy.deepcopy(self.data)
        data['plot'] = value
        self.data = data

    def reset(self):
        self.datasets = []

    def _add_dataset(self, dataset):
        """
        Adds the dataset to the datasets array.

        Args:
            dataset(dict): The data.
        """
        datasets = self.datasets
        datasets.append(dataset)
        self.datasets = datasets

    def _add_plot(self, plot_object):
        """
        Update plot object.

        Args:
            plot_object(dict): The plot.
        """
        self.plot = plot_object

    def add_series(self, title, data):
        """
        Add plot series into plot dataset. We assume that the first column is x and second column is y

        Args:
            title: series name
            data: plot data. Support different types of data: 2-D list, 2-D Numpy array and pandas dataframe with 2 col.
        """

        if not title:
            raise ValueError('The argument "title" is required.')

        if isinstance(data, pd.DataFrame):
            if data.empty:
                raise ValueError('The pandas.DataFrame must not be empty.')
        else:
            if not data:
                raise ValueError('The argument "data" is required.')

        d = {
            'dataset': data,
            'title': title,

        }
        self._add_dataset(d)

    def plot_from_dataframe(self, data_frame, series_axes=None, series_labels=None):
        """
        Adds a pandas.DataFrame with multiple columns to the result.

        Args:
            data_frame(pandas.DataFrame): The data.
            series_axes(list): A list of tuple label for x and y axes respectively.
             For example: [('x', 'y'), ('x1', 'y1)]. if plot axes is not provided,
             the first column is x and the rest are ys.
            series_labels(list): A list of series' label. For example: ['Series 1', 'Series 2', 'Series 3'].
        """
        series_axes = [] if series_axes is None else series_axes
        series_labels = [] if series_labels is None else series_labels

        if not isinstance(data_frame, pd.DataFrame):
            raise ValueError('The argument "data_frame" must be a pandas.DataFrame.')

        if data_frame.empty:
            raise ValueError('The pandas.DataFrame must not be empty.')

        d = {
            'dataset': data_frame,
            'series_axes': series_axes,
            'series_labels': series_labels,
        }
        self._add_dataset(d)

    def add_plot(self, plot):
        """
        Adds a plotly plot object to the result.

        Args:
            plot(obj): plotly figure. Only support adding one plot.
        """

        if not isinstance(plot, go.Figure):
            raise ValueError('The argument "plot" must be a plotly Figure.')

        plot_object = {
            'plot_object': plot,
        }

        self._add_plot(plot_object)

    def get_plot_object(self):
        """
        Gets plot object from the result.

        Returns plot object.
        """

        datasets = self.datasets
        plot_object = self.plot
        options = self.options
        renderer = options.get('renderer', 'plotly')
        plot_type = options.get('plot_type', 'lines')
        axis_labels = options.get('axis_labels', ['x', 'y'])
        line_shape = options.get('line_shape', 'linear')
        x_axis_type = options.get('x_axis_type', 'linear')

        # Handle the case where the user just provide a plotly object.
        if isinstance(plot_object, dict):
            if 'plot_object' in plot_object.keys():
                # Only support Plotly for now because we can't serialize bokeh plot.
                return plot_object['plot_object']

        plot_figure = None
        # Set layout such as axis label for x and y axis.
        if renderer == 'bokeh':
            plot_figure = figure(x_axis_type=x_axis_type, width=900)
            plot_figure.xaxis.axis_label = axis_labels[0]
            plot_figure.yaxis.axis_label = axis_labels[1]
        elif renderer == 'plotly':
            plot_figure = go.Figure(layout=go.Layout(xaxis={'title': {'text': axis_labels[0]}},
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
                    series_axes.extend((column_names[0], col) for col in column_names[1:])

            # Create default series label for panda dataframe with multiple columns.
            if 'series_labels' in ds.keys():
                series_labels = ds['series_labels']
                if not series_labels:
                    for _i in range(len(series_axes)):
                        series_labels.append(f"Data Series {label_count}")
                        label_count += 1
            if 'dataset' in ds.keys():
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
                            plot_figure.line("x", "y", source=ColumnDataSource(data), legend_label=series_label,
                                             color=Category10[10][plot_count % 10])
                        elif plot_type == 'scatter':
                            plot_figure.scatter("x", "y", source=ColumnDataSource(data), legend_label=series_label,
                                                color=Category10[10][plot_count % 10])
                        elif plot_type == 'bar':
                            plot_figure.vbar(x="x", y="y", source=ColumnDataSource(data), legend_label=series_label,
                                             color=Category10[10][plot_count % 10])
                        plot_count += 1
                else:
                    for i, axis in enumerate(series_axes):
                        # Handle panda dataframe with multiple columns
                        if isinstance(series_labels, list):
                            series_label = series_labels[i]

                        if isinstance(plot_data, pd.DataFrame):
                            x_axis = axis[0] if axis[0] == plot_data.columns[0] else plot_data.columns[0]
                            y_axis = axis[1] if axis[1] == plot_data.columns[1] else plot_data.columns[1]
                            x = plot_data[x_axis].to_list()
                            y = plot_data[y_axis].to_list()
                        else:
                            x = plot_data[0]
                            y = plot_data[1]

                        if plot_type == 'bar':
                            plot_figure.add_trace(go.Bar(x=x, y=y, name=series_label))
                            plot_figure.update_layout(xaxis=dict(type="category"))
                        else:
                            plot_mode = 'lines' if plot_type == 'lines' else 'markers'
                            plot_figure.add_trace(go.Scatter(x=x, y=y, name=series_label,
                                                             mode=plot_mode, line_shape=line_shape))

        return plot_figure
