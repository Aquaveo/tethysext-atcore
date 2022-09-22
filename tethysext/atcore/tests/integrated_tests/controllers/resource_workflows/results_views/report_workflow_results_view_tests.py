from unittest import mock
import pandas as pd
from tethysext.atcore.controllers.resource_workflows.map_workflows.map_workflow_view import MapWorkflowView
from tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view import ReportWorkflowResultsView
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult, DatasetWorkflowResult, \
    PlotWorkflowResult


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ReportWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = ReportWorkflowResultsView()

    @mock.patch.object(ResourceWorkflowView, 'get_step')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_get_context(self, mock_sup_get_context, mock_mapWV_get_context, mock_get_current_step_result):
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

        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

    @mock.patch.object(ReportWorkflowResultsView, 'get_managers')
    @mock.patch.object(ResourceWorkflowView, 'is_read_only')
    @mock.patch.object(MapWorkflowView, 'process_step_options')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_process_step_options_dataframe(self, mock_sup_get_context, mock_mapWV_get_context, _,
                                            mock_is_read_only, mock_get_managers):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_is_read_only.return_value = False
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

        self.instance.process_step_options(
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
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['dataset']['data_description'],
                         'test description')

    @mock.patch.object(ReportWorkflowResultsView, 'get_managers')
    @mock.patch.object(ResourceWorkflowView, 'is_read_only')
    @mock.patch.object(MapWorkflowView, 'process_step_options')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_process_step_options_plot(self, mock_sup_get_context, mock_mapWV_get_context, _, mock_is_read_only,
                                       mock_get_managers):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_is_read_only.return_value = False

        mock_data = PlotWorkflowResult(
            name='Cross Section of Stream',
            codename='plot_data',
            description='Description for result 4',
            order=40,
            options={
                'no_dataset_message': 'No data to view...',
                'renderer': 'bokeh',
                'plot_type': 'lines',
                'line_shape': 'spline',
                'axis_labels': ['Distance from left bank (ft)', 'Depth (ft)'],
            },
        )
        mock_current_step.results = mock_data

        reach_9 = [[0, 1101.88, 2998.66, 4842.02, 6367.66, 7792.57, 8500], [3, 2.46, 0.17, 0.3, 0.41, 0.76, 3]]
        water_surface = [[270, 8480], [2.9, 2.9]]

        mock_data.add_series('Reach 9', reach_9)
        mock_data.add_series('Water Surface', water_surface)
        mock_current_step.results = [mock_data]

        mock_get_managers.return_value = ['model_db', 'map_manager']

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_result.datasets = [{
            'title': 'series title',
            'dataset': mock_pandas_data,
        }]
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh']
        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        self.instance.process_step_options(
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
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['plot']['name'],
                         'Cross Section of Stream')
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['plot']['description'],
                         'Description for result 4')
        self.assertIn('Distance from left bank (ft)',
                      mock_context.update.call_args[0][0]['report_results'][0]['plot']['plot']['script'])

    @mock.patch.object(ReportWorkflowResultsView, 'get_managers')
    @mock.patch.object(ResourceWorkflowView, 'is_read_only')
    @mock.patch.object(MapWorkflowView, 'process_step_options')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_process_step_options_map(self, mock_sup_get_context, mock_mapWV_get_context, _, mock_is_read_only,
                                      mock_get_managers):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = {'layer_groups': [{"id": "depth", "layers": [{"options": {"params": mock.MagicMock()}}]}],
                        'map_view': mock.MagicMock()}
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_geoserver = mock.MagicMock()
        mock_map_manager = mock.MagicMock()
        mock_spatial_manager = mock.MagicMock()
        mock_is_read_only.return_value = False

        mock_data = SpatialWorkflowResult(
            name='Test Name',
            codename='test_codename',
            description='Test description',
            order=10,
            options={
                'layer_group_title': 'Test Legend Title',
            },
            geoserver_name=mock_geoserver,
            map_manager=mock_map_manager,
            map_renderer='cesium_map_view',
            spatial_manager=mock_spatial_manager,
            controller='tethysapp.steem.controllers.map_view.steem_result_map_view.SteemResultMapView',
        )

        mock_data.layers = [{'type': 'wms', 'endpoint': 'http://admin:geoserver@192.168.99.163:8181/geoserver/wms/',
                             'layer_name': 'steem:depth_test', 'layer_title': '100yr_flow_depth_10m',
                             'layer_variable': 'depth', 'viewparams': None, 'env': None, 'layer_id': '',
                             'visible': True, 'tiled': True, 'public': True, 'geometry_attribute': 'geometry',
                             'selectable': False, 'plottable': False, 'has_action': False,
                             'extent': [-122.33193, 47.090354, -122.595756, 47.17121], 'popup_title': None,
                             'excluded_properties': None}]
        mock_current_step.results = [mock_data]

        mock_get_managers.return_value = ['model_db', mock_map_manager]
        mock_options = {'url': 'http://admin:geoserver@192.168.99.163:8181/geoserver/wms/',
                        'params': {'LAYERS': 'steem:depth_test', 'TILED': True,
                                   'TILESORIGIN': '0.0,0.0'}, 'serverType': 'geoserver',
                        'crossOrigin': 'anonymous',
                        'tileGrid': {'resolutions': [0, 0],
                                     'extent': [0, 1, 2, 3],
                                     'origin': [0.0, 0.0], 'tileSize': [256, 256]}}
        mock_build_wms_layer = mock.MagicMock(source='TileWMS', legend_title='100yr_flow_depth_10m',
                                              options=mock_options)
        mock_map_manager.build_wms_layer.return_value = mock_build_wms_layer
        mock_map_manager.build_legend.return_value = "legend_wms"

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', 'lines', ['x', 'y'], 'linear', 'linear', 'page title',
                                        'No dataset found.']
        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        self.instance.process_step_options(
            request=mock_request,
            session=mock_session,
            context=mock_context,
            resource=mock_resource,
            current_step=mock_current_step,
            previous_step=mock_previous_step,
            next_step=mock_next_step,
        )

        self.assertEqual(mock_context['can_run_workflows'], True)
        self.assertEqual(mock_context['has_tabular_data'], False)
        self.assertEqual(mock_context['report_results'][0]['map']['name'], "Test Name")
        self.assertEqual(mock_context['report_results'][0]['map']['description'], "Test description")
        self.assertEqual(mock_context['report_results'][0]['map']['legend'], 'legend_wms')

        self.assertEqual(mock_context['report_results'][0]['map']['map'], [mock_build_wms_layer])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.report_workflow_results_view.log')
    @mock.patch.object(ReportWorkflowResultsView, 'get_managers')
    @mock.patch.object(ResourceWorkflowView, 'is_read_only')
    @mock.patch.object(MapWorkflowView, 'process_step_options')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_process_step_options_map_wrong_type(self, mock_sup_get_context, mock_mapWV_get_context, _,
                                                 mock_is_read_only, mock_get_managers, mock_log):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = {'layer_groups': [{"id": "depth", "layers": [{"options": {"params": mock.MagicMock()}}]}],
                        'map_view': mock.MagicMock()}
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_geoserver = mock.MagicMock()
        mock_map_manager = mock.MagicMock()
        mock_spatial_manager = mock.MagicMock()
        mock_is_read_only.return_value = False

        mock_data = SpatialWorkflowResult(
            name='Test Name',
            codename='test_codename',
            description='Test description',
            order=10,
            options={
                'layer_group_title': 'Test Legend Title',
            },
            geoserver_name=mock_geoserver,
            map_manager=mock_map_manager,
            map_renderer='cesium_map_view',
            spatial_manager=mock_spatial_manager,
            controller='tethysapp.steem.controllers.map_view.steem_result_map_view.SteemResultMapView',
        )

        mock_data.layers = [{'type': 'test_type'}]
        mock_current_step.results = [mock_data]

        mock_get_managers.return_value = ['model_db', mock_map_manager]

        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        self.instance.process_step_options(
            request=mock_request,
            session=mock_session,
            context=mock_context,
            resource=mock_resource,
            current_step=mock_current_step,
            previous_step=mock_previous_step,
            next_step=mock_next_step,
        )
        mock_log.warning.assert_called_with('Unsupported layer type will be skipped: test_type')

    @mock.patch.object(ReportWorkflowResultsView, 'get_managers')
    @mock.patch.object(ResourceWorkflowView, 'is_read_only')
    @mock.patch.object(MapWorkflowView, 'process_step_options')
    @mock.patch.object(MapWorkflowView, 'get_context')
    @mock.patch.object(WorkflowResultsView, 'get_context')
    def test_process_step_options_map_geojson(self, mock_sup_get_context, mock_mapWV_get_context, _, mock_is_read_only,
                                              mock_get_managers):
        mock_resource = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_current_step = mock.MagicMock()
        mock_previous_step = mock.MagicMock()
        mock_next_step = mock.MagicMock()
        mock_plot = mock.MagicMock(return_value='BokehView')
        mock_result = mock.MagicMock(get_plot_object=mock_plot)
        mock_geoserver = mock.MagicMock()
        mock_map_manager = mock.MagicMock()
        mock_spatial_manager = mock.MagicMock()
        mock_is_read_only.return_value = False

        mock_data = SpatialWorkflowResult(
            name='Depth',
            codename='depth',
            description='Description for result 2',
            order=10,
            options={
                'layer_group_title': 'Depth',
            },
            geoserver_name=mock_geoserver,
            map_manager=mock_map_manager,
            map_renderer='cesium_map_view',
            spatial_manager=mock_spatial_manager,
            controller='tethysapp.steem.controllers.map_view.steem_result_map_view.SteemResultMapView',
        )

        mock_data.layers = [{'type': 'geojson', 'endpoint': 'http://admin:geoserver@192.168.99.163:8181/geoserver/wms/',
                             'layer_name': 'steem:depth_test', 'layer_title': '100yr_flow_depth_10m',
                             'layer_variable': 'depth', 'viewparams': None, 'env': None, 'layer_id': '',
                             'visible': True, 'tiled': True, 'public': True, 'geometry_attribute': 'geometry',
                             'selectable': False, 'plottable': False, 'has_action': False,
                             'extent': [-122.33193, 47.090354, -122.595756, 47.17121], 'popup_title': None,
                             'excluded_properties': None}]
        mock_current_step.results = [mock_data]

        mock_get_managers.return_value = ['model_db', mock_map_manager]
        mock_build_geojson_layer = mock.MagicMock()
        mock_map_manager.build_geojson_layer.return_value = mock_build_geojson_layer
        mock_map_manager.build_legend.return_value = 'legend'

        mock_pandas_data = mock.MagicMock(spec=pd.DataFrame)
        mock_pandas_data.columns = ['foo', 'bar', 'baz']
        mock_result.name = 'title'
        mock_options = mock.MagicMock(get=mock.MagicMock())
        mock_result.options = mock_options
        mock_options.get.side_effect = ['bokeh', 'ft']
        mock_sup_get_context.return_value = {}
        mock_mapWV_get_context.return_value = {}

        self.instance.process_step_options(
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
        self.assertEqual(mock_context.update.call_args[0][0]['report_results'][0]['map'],
                         {'name': 'Depth', 'description': 'Description for result 2', 'legend': 'legend',
                          'map': [mock_build_geojson_layer]})
