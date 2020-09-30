"""
********************************************************************************
* Name: dataset_workflow_result.py
* Author: nswain
* Created On: June 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import copy
import pandas as pd
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult


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
        Returns default options dictionary for the object.
        """
        default_options = super().default_options
        default_options.update({
            'data_table_kwargs': {
                'searching': False,
                'paging': False,
                'info': False
            },
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

    def add_pandas_dataframe(self, title, data_frame, axes, plot_lib='bokeh'):
        """
        Adds a pandas.DataFrame to the result.

        Args:
            title(str): Display name.
            data_frame(pandas.DataFrame): The data.
            axes(list): A list of tuples for pair axis ex: ([('x', 'y'), ('x1', 'y1'), ('x', 'y2')])
            plot_lib(enum): either "bokeh" or "plotly"
        """

        if not title:
            raise ValueError('The argument "title" is required.')

        if not isinstance(data_frame, pd.DataFrame):
            raise ValueError('The argument "data_frame" must be a pandas.DataFrame.')

        if data_frame.empty:
            raise ValueError('The pandas.DataFrame must not be empty.')

        d = {
            'title': title,
            'dataset': data_frame,
            'plot_lib': plot_lib,
            'axes': axes
        }
        self._add_dataset(d)
