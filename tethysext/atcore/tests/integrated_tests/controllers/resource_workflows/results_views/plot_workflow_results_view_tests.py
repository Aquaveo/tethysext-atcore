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

    @mock.patch(
        'tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.plot_workflow_results_view.PlotWorkflowResultView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context(self, mock_sup_get_context, mock_get_result, mock_bokeh):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_bokeh = mock.MagicMock()
        mock_bokeh.return_value = 'PlotView'
        mock_get_result.return_value = mock_result

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'bar'
        mock_result.datasets = [{
            'dataset': mock_pandas_data,
            'title': 'series title',
        }]
        mock_options = mock.MagicMock(plot_lib='bokeh', axes=[('x', 'y')], labels=['Series 1'], height=500, width=800,
                                      plot_type='lines')
        mock_result.options = mock_options
        baseline = {
            'no_dataset_message': 'No dataset found.',
            'page_title': 'bar',
            'datasets': [{
                'dataset': mock_pandas_data,
                'title': 'series title',
            }],
            'plot_view_input': 'PlotView',
        }
        mock_options.get.side_effect = ['bokeh', [('x', 'y')], ['Series 1'], 'bar',  500, 800, 'lines',
                                        'No dataset found.']
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
            mock.call('page_title', 'bar'),
            mock.call('height', 500),
            mock.call('width', 800),
            mock.call('plot_type', 'lines'),
            mock.call('no_dataset_message', 'No dataset found.')],
        )
        self.assertDictEqual(baseline, ret)
