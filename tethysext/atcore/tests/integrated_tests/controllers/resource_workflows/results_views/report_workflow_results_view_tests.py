from unittest import mock
import pandas as pd
from tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view import ReportWorkflowResultsView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from datetime import datetime
import numpy as np


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ReportWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = ReportWorkflowResultsView()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view.ReportWorkflowResultView.get_result')  # noqa: E501
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
        breakpoint()
        mock_bokeh.return_value = 'BokehView'
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
        mock_options.get.side_effect = ['page title', 'bokeh', 'lines', ['x', 'y'], 'linear', 'linear',
                                        'No dataset found.']
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'datasets': [{
                'title': 'series title',
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
            mock.call('page_title', 'title'),
            mock.call('renderer', 'plotly'),
            mock.call('plot_type', 'lines'),
            mock.call('axis_labels', ['x', 'y']),
            mock.call('line_shape', 'linear'),
            mock.call('x_axis_type', 'linear'),
            mock.call('no_dataset_message', 'No dataset found.')],
        )

        self.assertEqual(baseline['no_dataset_message'], ret['no_dataset_message'])
        self.assertEqual(baseline['plot_view_input'], ret['plot_view_input'])
        self.assertEqual(baseline['datasets'], ret['datasets'])

