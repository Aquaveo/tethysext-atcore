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
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult
import plotly.graph_objs as go

__all__ = ['PlotWorkflowResult']


class PlotWorkflowResult(ResourceWorkflowResult):
    """
    Data model for storing spatial information about resource workflow results.
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
        Options:
            renderer (str): bokeh or plotly
            axes(list): A list of tuples for pair axis ex. For example: [('x', 'y'), ('x1', 'y1'), ('x', 'y2')]
            axis_labels(list): A list of label for x and y axes respectively. For example: ['x', 'y']
            plot_type (str): lines or scatter
            line_shape (str): Only for plotly. You can select from on of these options: linear, spline, vhv, hvh, vh, hv
            x_axis_type (str): type of x axis. Available options are 'linear' or 'datetime'
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
        Add plot series into plot dataset.

        Args:
            title: series name
            data: plot data. Support different types of data: 2-D list, 2-D Numpy array and pandas dataframe.
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

    def plot_from_dataframe(self, data_frame, plot_axes=[], series_labels=[]):
        """
        Adds a pandas.DataFrame to the result.

        Args:
            data_frame(pandas.DataFrame): The data. if plot axes is not provided,
             the first column is x and the rest are ys.
            plot_axes(list): A list of tuple label for x and y axes respectively.
             For example: [('x', 'y'), ('x1', 'y1)].
            series_labels(list): A list of series' label. For example: ['Series 1', 'Series 2', 'Series 3'].
        """
        if not isinstance(data_frame, pd.DataFrame):
            raise ValueError('The argument "data_frame" must be a pandas.DataFrame.')

        if data_frame.empty:
            raise ValueError('The pandas.DataFrame must not be empty.')

        d = {
            'dataset': data_frame,
            'plot_axes': plot_axes,
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
