from unittest import mock
import pandas as pd
from tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view import PlotWorkflowResultView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from datetime import datetime
import numpy as np


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class PlotWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = PlotWorkflowResultView()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_bokeh(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_result.datasets = [{
            'title': 'series title',
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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
            mock.call('page_title', 'title'),
            mock.call('no_dataset_message', 'No dataset found.')],
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_plotly(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='PlotlyView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        mock_pandas_data_x = mock.MagicMock(spec=pd.DataFrame, to_list=mock.MagicMock())
        mock_pandas_data_y = mock.MagicMock(spec=pd.DataFrame, to_list=mock.MagicMock())
        mock_pandas_data_x.to_list.side_effect = [[1, 2, 3]]
        mock_pandas_data_y.to_list.side_effect = [[4, 5, 6]]
        mock_result.name = 'page_title'
        data_test = [[datetime(2020, 1, 1), 5], [datetime(2020, 1, 2), 6], [datetime(2020, 1, 3), 7],
                     [datetime(2020, 1, 4), 8], [datetime(2020, 1, 5), 9], [datetime(2020, 1, 6), 10]]

        df = pd.DataFrame(data=data_test)
        mock_result.datasets = [{
            'title': 'series title',
            'dataset': df,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_plot_object(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='PlotlyView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        mock_result.name = 'page_title'
        mock_result.datasets = [{
            'plot_object': 'plot_object',
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_bokeh_add_series_list(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        data_test = [[datetime(2020, 1, 2), datetime(2020, 1, 3), datetime(2020, 1, 4), datetime(2020, 1, 5),
                      datetime(2020, 1, 6), datetime(2020, 1, 7)], [2, 3, 4, 5, 6, 7]]

        mock_result.datasets = [{
            'title': 'series title',
            'dataset': data_test,
        }]

        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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
        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_bokeh_scatter_add_series_list(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        data_test = [[datetime(2020, 1, 2), datetime(2020, 1, 3), datetime(2020, 1, 4), datetime(2020, 1, 5),
                      datetime(2020, 1, 6), datetime(2020, 1, 7)], [2, 3, 4, 5, 6, 7]]

        mock_result.datasets = [{
            'title': 'series title',
            'dataset': data_test,
        }]

        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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
        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_add_series_list(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='PlotlyView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        data_test = [[datetime(2020, 1, 2), datetime(2020, 1, 3), datetime(2020, 1, 4), datetime(2020, 1, 5),
                      datetime(2020, 1, 6), datetime(2020, 1, 7)], [2, 3, 4, 5, 6, 7]]

        mock_result.datasets = [{
            'title': 'series title',
            'dataset': data_test,
        }]

        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_add_series_numpy(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='PlotlyView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        data_test = [np.arange('2020-01-02', '2020-01-07', dtype='datetime64[D]'), np.array([1, 2, 3, 4, 5, 6])]

        mock_result.datasets = [{
            'title': 'series title',
            'dataset': data_test,
        }]

        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_add_series_pandas_multiple_columns(self, mock_sup_get_context, mock_get_result):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='PlotlyView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_get_result.return_value = mock_result

        data_test = {
            'x': [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3), datetime(2020, 1, 4),
                  datetime(2020, 1, 5), datetime(2020, 1, 6)],
            'y': [2, 4, 8, 16, 25, 36],
            'y2': [3, 3*3, 9*3, 27*3, 9*3, 9],
        }
        data_test = pd.DataFrame(data=data_test)

        mock_result.datasets = [{
            'dataset': data_test,
            'series_axes': [('x', 'y'), ('x', 'y1'), ('x', 'y2')],
            'series_labels':['s1', 's2', 's3'],
        }]

        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['page title', 'No dataset found.']
        baseline = {
            'page_title': 'page title',
            'no_dataset_message': 'No dataset found.',
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
