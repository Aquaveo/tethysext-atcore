from unittest import mock
import pandas as pd
from datetime import datetime as dt
from tethysext.atcore.models.resource_workflow_results import PlotWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
import plotly.graph_objs as go
from bokeh.plotting import figure


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class PlotWorkflowResultTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = PlotWorkflowResult(name='test')

    def bind_instance_to_session(self):
        self.session.add(self.instance)
        self.session.commit()

    def test_default_options(self):
        baseline = {
            'renderer': 'plotly',
            'axes': [],
            'plot_type': 'lines',
            'axis_labels': ['x', 'y'],
            'line_shape': 'linear',
            'x_axis_type': 'datetime',
            'no_dataset_message': 'No dataset found.'
        }
        self.assertDictEqual(baseline, self.instance.default_options)

    def test_datasets(self):
        self.assertDictEqual({}, self.instance.data)
        ret = self.instance.datasets
        self.assertListEqual([], ret)

    def test_reset(self):
        self.instance.data['datasets'] = 'Bad data to reset'
        self.instance.reset()
        ret = self.instance.data['datasets']
        self.assertEqual([], ret)

    def test__add_dataset(self):
        test_data = 'Test data'
        self.instance._add_dataset(test_data)
        self.assertListEqual([test_data], self.instance.datasets)

    def test__add_plot(self):
        test_data = 'Test plot'
        self.instance._add_plot(test_data)
        self.assertEqual(test_data, self.instance.plot)

    def test_datasets_bound(self):
        self.bind_instance_to_session()
        self.test_datasets()

    def test_reset_datasets_bound(self):
        self.bind_instance_to_session()
        self.test_reset()

    def test__add_dataset_bound(self):
        self.bind_instance_to_session()
        self.test__add_dataset()

    def test_add_series_no_title(self):
        self.assertRaises(ValueError, self.instance.add_series, '', ['test'])

    def test_add_series_no_data(self):
        self.assertRaises(ValueError, self.instance.add_series, 'title', '')

    def test_add_series_empty_data_frame(self):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=True)
        self.assertRaises(ValueError, self.instance.add_series, 'title', mock_dataframe)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult._add_dataset')  # noqa: E501
    def test_add_series(self, mock_add_dataset):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=False)
        self.instance.add_series('series title', mock_dataframe)
        baseline = {
            'title': 'series title',
            'dataset': mock_dataframe,
        }
        mock_add_dataset.assert_called_with(baseline)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult._add_dataset')  # noqa: E501
    def test_plot_from_dataframe(self, mock_add_dataset):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=False)
        self.instance.plot_from_dataframe(mock_dataframe)
        baseline = {
            'dataset': mock_dataframe,
            'series_axes': [],
            'series_labels': []
        }
        mock_add_dataset.assert_called_with(baseline)

    def test_plot_from_dataframe_not_dataframe(self):
        self.assertRaises(ValueError, self.instance.plot_from_dataframe, ['test'])

    def test_plot_from_dataframe_empty_dataframe(self):
        mock_dataframe = mock.MagicMock(spec=pd.DataFrame, empty=True)
        self.assertRaises(ValueError, self.instance.plot_from_dataframe, mock_dataframe)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult._add_plot')  # noqa: E501
    def test_add_plot(self, mock_add_dataset):
        mock_plot = mock.MagicMock(spec=go.Figure, empty=False)
        self.instance.add_plot(mock_plot)
        baseline = {
            'plot_object': mock_plot,
        }
        mock_add_dataset.assert_called_with(baseline)

    def test_add_plot_not_plolty(self):
        self.assertRaises(ValueError, self.instance.add_plot, 'foo')

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult.options')
    def test_get_plot_object_dict(self, mock_options):
        mock_plotly_plot = mock.MagicMock(spec=go.Figure, empty=False)
        mock_options.get = mock.MagicMock(side_effect=['plotly', 'lines', ['x', 'y'], 'linear', 'linear'])

        self.instance.add_plot(mock_plotly_plot)

        ret_plot = self.instance.get_plot_object()

        self.assertEqual(ret_plot, mock_plotly_plot)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult.options')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.figure')
    def test_get_plot_object_bokeh_line(self, mock_bokeh_figure, mock_options):
        mock_bokeh_plot = mock.MagicMock(
            spec=figure, xaxis=mock.MagicMock(axis_label='x'), yaxis=mock.MagicMock(axis_label='y'),
            line=mock.MagicMock(return_value='test line type')
        )
        mock_bokeh_figure.return_value = mock_bokeh_plot
        mock_dataframe = pd.DataFrame({
            'x': [dt(2020, 1, 2), dt(2020, 1, 3), dt(2020, 1, 4), dt(2020, 1, 5), dt(2020, 1, 6), dt(2020, 1, 7)],
            'y': [2, 3, 4, 5, 6, 7]
        })
        mock_datasets = [{
            'title': 'Test Title',
            'series_axes': [('x', 'y')],
            'series_labels': ['test_label'],
            'dataset': mock_dataframe
        }]
        mock_options.get = mock.MagicMock(side_effect=['bokeh', 'lines', ['x', 'y'], 'linear', 'linear'])

        self.instance.plot = mock_bokeh_plot
        self.instance.datasets = mock_datasets

        ret_plot = self.instance.get_plot_object()

        self.assertEqual(ret_plot, mock_bokeh_plot)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult.options')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.figure')
    def test_get_plot_object_bokeh_scatter(self, mock_bokeh_figure, mock_options):
        mock_bokeh_plot = mock.MagicMock(
            spec=figure, xaxis=mock.MagicMock(axis_label='x'), yaxis=mock.MagicMock(axis_label='y'),
            scatter=mock.MagicMock(return_value='test scatter type')
        )
        mock_bokeh_figure.return_value = mock_bokeh_plot
        mock_dataframe = pd.DataFrame(
            {'x': [dt(2020, 1, 2), dt(2020, 1, 3), dt(2020, 1, 4)], 'y': [2, 3, 4]},
            columns=['x', 'y']
        )
        mock_datasets = [{
            'title': 'Test Title',
            'series_axes': [],
            'series_labels': [],
            'dataset': mock_dataframe
        }]
        mock_options.get = mock.MagicMock(side_effect=['bokeh', 'scatter', ['x', 'y'], 'linear', 'linear'])

        self.instance.plot = mock_bokeh_plot
        self.instance.datasets = mock_datasets

        ret_plot = self.instance.get_plot_object()

        self.assertEqual(ret_plot, mock_bokeh_plot)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult.options')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.go.Figure')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.go.Scatter')
    def test_get_plot_object_plotly_line(self, mock_scatter_plot, mock_plotly_figure, mock_options):
        mock_plotly_plot = mock.MagicMock(
            spec=go.Figure, xaxis=mock.MagicMock(axis_label='x'), yaxis=mock.MagicMock(axis_label='y'),
            add_trace=mock.MagicMock(return_value=mock_scatter_plot)
        )
        mock_plotly_figure.return_value = mock_plotly_plot
        mock_dataframe = pd.DataFrame({
            'x': [dt(2020, 1, 2), dt(2020, 1, 3), dt(2020, 1, 4), dt(2020, 1, 5), dt(2020, 1, 6), dt(2020, 1, 7)],
            'y': [2, 3, 4, 5, 6, 7]
        })
        mock_datasets = [{
            'title': 'Test Title',
            'series_axes': [('x', 'y')],
            'series_labels': ['test_label'],
            'dataset': mock_dataframe
        }]
        mock_options.get = mock.MagicMock(side_effect=['plotly', 'lines', ['x', 'y'], 'linear', 'linear'])

        self.instance.plot = mock_plotly_plot
        self.instance.datasets = mock_datasets

        ret_plot = self.instance.get_plot_object()

        self.assertEqual(ret_plot, mock_plotly_plot)

    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.PlotWorkflowResult.options')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.go.Figure')
    @mock.patch('tethysext.atcore.models.resource_workflow_results.plot_workflow_result.go.Scatter')
    def test_get_plot_object_plotly_list_dataset(self, mock_scatter_plot, mock_plotly_figure,
                                                 mock_options):
        mock_plotly_plot = mock.MagicMock(
            spec=go.Figure, xaxis=mock.MagicMock(axis_label='x'), yaxis=mock.MagicMock(axis_label='y'),
            add_trace=mock.MagicMock(return_value=mock_scatter_plot)
        )
        mock_plotly_figure.return_value = mock_plotly_plot
        mock_dataset = [
            [dt(2020, 1, 2), dt(2020, 1, 3), dt(2020, 1, 4), dt(2020, 1, 5), dt(2020, 1, 6), dt(2020, 1, 7)],
            [2, 3, 4, 5, 6, 7]
        ]
        mock_datasets = [{
            'title': 'Test Title',
            'series_axes': [('x', 'y')],
            'series_labels': ['test_label'],
            'dataset': mock_dataset
        }]
        mock_options.get = mock.MagicMock(side_effect=['plotly', 'scatter', ['x', 'y'], 'linear', 'linear'])

        self.instance.plot = mock_plotly_plot
        self.instance.datasets = mock_datasets

        ret_plot = self.instance.get_plot_object()

        self.assertEqual(ret_plot, mock_plotly_plot)
