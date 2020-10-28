from unittest import mock
import pandas as pd
from tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view import ReportWorkflowResultsView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult, DatasetWorkflowResult, \
    PlotWorkflowResult
from tethys_sdk.gizmos import DataTableView
from collections import OrderedDict


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ReportWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = ReportWorkflowResultsView()

    @mock.patch('tethysext.atcore.controllers.utilities.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.get_step')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context(self, mock_sup_get_context, mock_mapWV_get_context, mock_get_current_step_result, mock_bokeh):
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
        mock_get_current_step_result.return_value = mock_result

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_result.datasets = [{
            'title': 'series title',
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', 'lines', ['x', 'y'], 'linear', 'linear', 'page title',
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
        mock_mapWV_get_context.return_value = {}

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

    @mock.patch('tethysext.atcore.controllers.utilities.get_tabular_data_for_previous_steps')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.utilities.BokehView')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view.ReportWorkflowResultsView.get_managers')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.is_read_only')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.MapWorkflowView.process_step_options')   # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_process_step_options(self, mock_sup_get_context, mock_mapWV_get_context, _,
                                  mock_is_read_only, mock_get_managers, mock_bokeh, mock_tabular):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_is_read_only.return_value = False
        mock_bokeh.return_value = 'BokehView'
        mock_tabular.return_value = 'tabular_data'
        data = [
            [
                'reach_1', 'reach_1', 'reach_11',
            ],
            [
                604.164, 1694.88, 622.768,
            ]
        ]

        dataset_title = "Test Title"
        df = pd.DataFrame(data, columns=['Col1', 'Col2', 'Col3'])

        mock_data = DatasetWorkflowResult(
            name='test_table_name',
            codename='test_table',
            description='test description',
            order=30,
            options={
                'no_dataset_message': 'No data to view...',
            },
        )

        mock_data.add_pandas_dataframe(dataset_title, df)
        mock_current_step.results = [mock_data]

        mock_get_managers.return_value = ['bokeh', 'lines']

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_result.datasets = [{
            'title': 'series title',
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', 'lines', ['x', 'y'], 'linear', 'linear', 'page title',
                                        'No dataset found.']
        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        ret = self.instance.process_step_options(
            request=mock_request,
            session=mock_session,
            context=mock_context,
            resource=mock_resource,
            current_step=mock_current_step,
            previous_step=mock_previous_step,
            next_step=mock_next_step,
        )

        self.assertEqual(mock_context.update.call_args[0][0]['can_run_workflows'], True)
        self.assertEqual(mock_context.update.call_args[0][0]['has_tabular_data'], False)
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['dataset']['dataset'], df)
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['dataset']['data_description'],
                         'test description')
