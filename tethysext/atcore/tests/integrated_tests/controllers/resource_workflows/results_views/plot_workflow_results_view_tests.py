from unittest import mock
import pandas as pd
from tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view import PlotWorkflowResultView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class PlotWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = PlotWorkflowResultView()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_bokeh(self, mock_sup_get_context, mock_get_result, mock_bokeh):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_bokeh.return_value = 'BokehView'
        mock_get_result.return_value = mock_result

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'bar'
        mock_result.datasets = [{
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', [('x', 'y')], ['Series 1'], 'lines', ['x', 'y'], 'linear',
                                        'No dataset found.']
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'datasets': [{
                'dataset': mock_pandas_data,
            }],
            'plot_view_input': 'BokehView',
        }
        mock_sup_get_context.return_value = {}

        ret = self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        # Test all things were called here
        mock_sup_get_context.assert_called_with(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        mock_get_result.assert_called_with(
            request=mock_request,
            result_id=mock_result_id,
            session=mock_session
        )

        mock_options.get.assert_has_calls([
            mock.call('plot_lib', 'bokeh'),
            mock.call('axes', []),
            mock.call('labels', []),
            mock.call('plot_type', 'lines'),
            mock.call('axis_labels', ['x', 'y']),
            mock.call('line_shape', 'linear'),
            mock.call('no_dataset_message', 'No dataset found.')],
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])
        self.assertEqual(baseline['datasets'], ret['datasets'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_bokeh_default_axes_labels(self, mock_sup_get_context, mock_get_result, mock_bokeh):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_bokeh.return_value = 'BokehView'
        mock_get_result.return_value = mock_result

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame, columns=mock.MagicMock())
        mock_pandas_data.columns.to_list.return_value = ['x', 'y', 'y1']
        mock_result.name = 'bar'
        mock_result.datasets = [{
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', [], [], 'lines', ['x', 'y'], 'linear',
                                        'No dataset found.']
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'datasets': [{
                'dataset': mock_pandas_data,
            }],
            'plot_view_input': 'BokehView',
        }
        mock_sup_get_context.return_value = {}

        ret = self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        # Test all things were called here
        mock_sup_get_context.assert_called_with(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        mock_get_result.assert_called_with(
            request=mock_request,
            result_id=mock_result_id,
            session=mock_session
        )

        mock_options.get.assert_has_calls([
            mock.call('plot_lib', 'bokeh'),
            mock.call('axes', []),
            mock.call('labels', []),
            mock.call('plot_type', 'lines'),
            mock.call('axis_labels', ['x', 'y']),
            mock.call('line_shape', 'linear'),
            mock.call('no_dataset_message', 'No dataset found.')],
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])
        self.assertEqual(baseline['datasets'], ret['datasets'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotlyView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_plotly(self, mock_sup_get_context, mock_get_result, mock_plotly):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_plotly.return_value = 'PlotlyView'
        mock_get_result.return_value = mock_result

        mock_pandas_data_x = mock.MagicMock(spec=pd.DataFrame, to_list=mock.MagicMock())
        mock_pandas_data_y = mock.MagicMock(spec=pd.DataFrame, to_list=mock.MagicMock())
        mock_pandas_data_x.to_list.side_effect = [[1, 2, 3]]
        mock_pandas_data_y.to_list.side_effect = [[4, 5, 6]]
        mock_result.name = 'bar'
        mock_result.datasets = [{
            'dataset': {'x': mock_pandas_data_x, 'y': mock_pandas_data_y},
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['plotly', [('x', 'y')], ['Series 1'], 'lines', ['x', 'y'], 'linear',
                                        'No dataset found.']
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'datasets': [{
                'dataset': {'x': mock_pandas_data_x, 'y': mock_pandas_data_y},
            }],
            'plot_view_input': 'PlotlyView',
        }
        mock_sup_get_context.return_value = {}

        ret = self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        # Test all things were called here
        mock_sup_get_context.assert_called_with(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        mock_get_result.assert_called_with(
            request=mock_request,
            result_id=mock_result_id,
            session=mock_session
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])
        self.assertEqual(baseline['datasets'], ret['datasets'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotlyView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_plot_object(self, mock_sup_get_context, mock_get_result, mock_plotly):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_plotly.return_value = 'PlotlyView'
        mock_get_result.return_value = mock_result

        mock_result.name = 'bar'
        mock_result.datasets = [{
            'plot_object': 'plot_object',
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['plotly', [('x', 'y')], ['Series 1'], 'lines', ['x', 'y'], 'linear',
                                        'No dataset found.']
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'datasets': [{
                'plot_object': 'plot_object',
            }],
            'plot_view_input': 'PlotlyView',
        }
        mock_sup_get_context.return_value = {}

        ret = self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        # Test all things were called here
        mock_sup_get_context.assert_called_with(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        mock_get_result.assert_called_with(
            request=mock_request,
            result_id=mock_result_id,
            session=mock_session
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])
        self.assertEqual(baseline['datasets'], ret['datasets'])