import copy
from unittest import mock
from django.http import JsonResponse
from tethys_sdk.gizmos import MapView
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view import MapWorkflowResultsView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MapWorkflowResultViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = MapWorkflowResultsView()

    def perpare_geojson_layers(self, with_plot=True):
        self.plot_title = 'Plot 1'
        self.plot_data = [
            {
                'name': 'Foo',
                'x': [2, 4, 6, 8],
                'y': [10, 15, 20, 25]
            },
            {
                'name': 'Bar',
                'x': [1, 3, 5, 9],
                'y': [9, 6, 12, 15]
            },
        ]
        self.plot_layout = {
            'foo': 'bar'
        }

        self.plot = {
            'title': self.plot_title,
            'data': self.plot_data,
            'layout': self.plot_layout
        }

        self.feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-87.87625096273638, 30.65151178301437]},
            'properties': {
                'id': 1,
            }
        }

        if with_plot:
            self.feature['properties']['plot'] = self.plot

        self.layer = {
            'type': 'geojson',
            'geojson':
                {
                    'type': 'FeatureCollection',
                    'crs': {},
                    'features': [self.feature]
                },
            'layer_name': '123_foo_bar',
            'layer_variable': 'foo_bar',
            'layer_title': 'Foo Bars',
            'popup_title': 'Foo Bar',
            'selectable': False
        }

        self.layer_no_type = copy.deepcopy(self.layer)
        self.layer_no_type.pop('type', None)

        return [self.layer]

    def prepare_wms_layers(self):
        self.layer = {
            'type': 'wms',
            'endpoint': 'http://foo.bar.com/wms',
            'layer_name': '123_foo_bar',
            'layer_variable': 'foo_bar',
            'layer_title': 'Foo Bars',
            'popup_title': 'Foo Bar',
            'selectable': False
        }

        self.layer_no_type = copy.deepcopy(self.layer)
        self.layer_no_type.pop('type', None)

        return [self.layer]

    def get_context_setup(self, mock_wrv_get_context, mock_mwv_get_context, mock_mwv_get_managers, mock_get_result,
                          initial_layer_groups, result_options, result_layers):
        self.mock_request = mock.MagicMock()
        self.mock_session = mock.MagicMock()
        self.mock_resource = mock.MagicMock()
        self.mock_model_database = mock.MagicMock(spec=ModelDatabase)
        self.mock_result = mock.MagicMock(
            spec=SpatialWorkflowResult,
            options=result_options,
            layers=result_layers
        )
        mock_get_result.return_value = self.mock_result
        mock_wrv_get_context.return_value = {
            'result_workflow_context': 'foo'
        }
        self.mock_map_view = mock.MagicMock(spec=MapView, layers=[{'layer_name': 'fake-layer'}],
                                            entities=[{'entity_name': 'fake-entities'}])
        mock_mwv_get_context.return_value = {
            'map_view': self.mock_map_view,
            'layer_groups': initial_layer_groups
        }
        self.mock_map_manager = mock.MagicMock(spec=MapManagerBase)
        mock_mwv_get_managers.return_value = (self.mock_model_database, self.mock_map_manager)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.set_feature_selection')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_managers')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_geojson(self, mock_wrv_get_context, mock_mwv_get_context, mock_mwv_get_managers,
                                 mock_mwv_set_feature_selection, mock_get_result):

        workflow_id = '123'
        step_id = '456'
        result_id = '789'
        result_layers = self.perpare_geojson_layers()
        initial_layer_groups = [{'id': 'fake-layer-group-1'}, {'id': 'fake-layer-group-2'}]
        opt_lg_title = 'Foo Results'
        opt_lg_control = 'radio'
        result_options = {
            'layer_group_title': opt_lg_title,
            'layer_group_control': opt_lg_control
        }

        self.get_context_setup(
            mock_wrv_get_context,
            mock_mwv_get_context,
            mock_mwv_get_managers,
            mock_get_result,
            initial_layer_groups,
            result_options,
            result_layers
        )

        instance = MapWorkflowResultsView()
        instance.map_type = 'map_view'
        ret = instance.get_context(
            request=self.mock_request,
            session=self.mock_session,
            resource=self.mock_resource,
            context={},
            model_db=self.mock_model_database,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id
        )

        self.assertIn('map_view', ret)
        self.assertIn('layer_groups', ret)
        self.assertIn('result_workflow_context', ret)
        mock_mwv_set_feature_selection.assert_called_with(map_view=self.mock_map_view, enabled=False)
        mock_get_result.assert_called_with(self.mock_request, result_id, self.mock_session)
        mock_mwv_get_managers.assert_called_with(request=self.mock_request, resource=self.mock_resource)

        self.mock_map_manager.build_geojson_layer.assert_called()
        self.mock_map_manager.build_layer_group.assert_called_with(
            id='workflow_results',
            display_name=opt_lg_title,
            layer_control=opt_lg_control,
            layers=[self.mock_map_manager.build_geojson_layer()]
        )
        self.assertEqual(2, len(self.mock_map_view.layers))
        self.assertEqual(self.mock_map_manager.build_geojson_layer(), self.mock_map_view.layers[0])
        self.assertEqual(self.mock_map_manager.build_layer_group(), ret['layer_groups'][0])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.set_feature_selection')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_managers')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_wms(self, mock_wrv_get_context, mock_mwv_get_context, mock_mwv_get_managers,
                             mock_mwv_set_feature_selection, mock_get_result):
        workflow_id = '123'
        step_id = '456'
        result_id = '789'
        result_layers = self.prepare_wms_layers()
        initial_layer_groups = [{'id': 'fake-layer-group-1'}, {'id': 'fake-layer-group-2'}]
        opt_lg_title = 'Foo Results'
        opt_lg_control = 'radio'
        result_options = {
            'layer_group_title': opt_lg_title,
            'layer_group_control': opt_lg_control
        }

        self.get_context_setup(
            mock_wrv_get_context,
            mock_mwv_get_context,
            mock_mwv_get_managers,
            mock_get_result,
            initial_layer_groups,
            result_options,
            result_layers
        )

        instance = MapWorkflowResultsView()
        instance.map_type = 'map_view'
        ret = instance.get_context(
            request=self.mock_request,
            session=self.mock_session,
            resource=self.mock_resource,
            context={},
            model_db=self.mock_model_database,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id
        )

        self.assertIn('map_view', ret)
        self.assertIn('layer_groups', ret)
        self.assertIn('result_workflow_context', ret)
        mock_mwv_set_feature_selection.assert_called_with(map_view=self.mock_map_view, enabled=False)
        mock_get_result.assert_called_with(self.mock_request, result_id, self.mock_session)
        mock_mwv_get_managers.assert_called_with(request=self.mock_request, resource=self.mock_resource)

        self.mock_map_manager.build_wms_layer.assert_called()
        self.mock_map_manager.build_layer_group.assert_called_with(
            id='workflow_results',
            display_name=opt_lg_title,
            layer_control=opt_lg_control,
            layers=[self.mock_map_manager.build_wms_layer()]
        )
        self.assertEqual(2, len(self.mock_map_view.layers))
        self.assertEqual(self.mock_map_manager.build_wms_layer(), self.mock_map_view.layers[0])
        self.assertEqual(self.mock_map_manager.build_layer_group(), ret['layer_groups'][0])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.translate_layers_to_cesium')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.set_feature_selection')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_managers')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_cesium(self, mock_wrv_get_context, mock_mwv_get_context, mock_mwv_get_managers,
                                mock_mwv_set_feature_selection, mock_get_result, mock_translate_layers_to_cesium):
        workflow_id = '123'
        step_id = '456'
        result_id = '789'
        result_layers = self.prepare_wms_layers()
        result_layers.extend(self.perpare_geojson_layers())
        initial_layer_groups = [{'id': 'fake-layer-group-1'}, {'id': 'fake-layer-group-2'}]
        opt_lg_title = 'Foo Results'
        opt_lg_control = 'radio'
        result_options = {
            'layer_group_title': opt_lg_title,
            'layer_group_control': opt_lg_control
        }

        self.get_context_setup(
            mock_wrv_get_context,
            mock_mwv_get_context,
            mock_mwv_get_managers,
            mock_get_result,
            initial_layer_groups,
            result_options,
            result_layers
        )

        mock_translate_layers_to_cesium.return_value = [[{'layer_name': 'fake-layer'}],
                                                        [{'entity_name': 'fake-entities'}]]
        instance = MapWorkflowResultsView()
        instance.map_type = 'cesium_map_view'
        ret = instance.get_context(
            request=self.mock_request,
            session=self.mock_session,
            resource=self.mock_resource,
            context={},
            model_db=self.mock_model_database,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id
        )

        self.assertIn('map_view', ret)
        self.assertIn('layer_groups', ret)
        self.assertIn('result_workflow_context', ret)
        mock_mwv_set_feature_selection.assert_called_with(map_view=self.mock_map_view, enabled=False)
        mock_get_result.assert_called_with(self.mock_request, result_id, self.mock_session)
        mock_mwv_get_managers.assert_called_with(request=self.mock_request, resource=self.mock_resource)

        self.mock_map_manager.build_wms_layer.assert_called()
        self.mock_map_manager.build_geojson_layer.assert_called()
        self.mock_map_manager.build_layer_group.assert_called_with(
            id='workflow_results',
            display_name=opt_lg_title,
            layer_control=opt_lg_control,
            layers=[self.mock_map_manager.build_wms_layer(), self.mock_map_manager.build_geojson_layer()]
        )
        self.assertEqual(2, len(self.mock_map_view.layers))
        self.assertEqual(2, len(self.mock_map_view.entities))
        self.assertEqual({'layer_name': 'fake-layer'}, self.mock_map_view.layers[0])
        self.assertEqual({'entity_name': 'fake-entities'}, self.mock_map_view.entities[0])
        self.assertEqual(self.mock_map_manager.build_layer_group(), ret['layer_groups'][0])

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.log')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.set_feature_selection')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_managers')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_context')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.WorkflowResultsView.get_context')  # noqa: E501
    def test_get_context_invalid_type(self, mock_wrv_get_context, mock_mwv_get_context, mock_mwv_get_managers,
                                      mock_mwv_set_feature_selection, mock_get_result, mock_log):
        workflow_id = '123'
        step_id = '456'
        result_id = '789'
        result_layers = [{'type': 'invalid-type'}]
        initial_layer_groups = [{'id': 'fake-layer-group-1'}, {'id': 'fake-layer-group-2'}]
        opt_lg_title = 'Foo Results'
        opt_lg_control = 'radio'
        result_options = {
            'layer_group_title': opt_lg_title,
            'layer_group_control': opt_lg_control
        }

        self.get_context_setup(
            mock_wrv_get_context,
            mock_mwv_get_context,
            mock_mwv_get_managers,
            mock_get_result,
            initial_layer_groups,
            result_options,
            result_layers
        )

        instance = MapWorkflowResultsView()
        ret = instance.get_context(
            request=self.mock_request,
            session=self.mock_session,
            resource=self.mock_resource,
            context={},
            model_db=self.mock_model_database,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id
        )

        self.assertIn('map_view', ret)
        self.assertIn('layer_groups', ret)
        self.assertIn('result_workflow_context', ret)
        mock_mwv_set_feature_selection.assert_called_with(map_view=self.mock_map_view, enabled=False)
        mock_get_result.assert_called_with(self.mock_request, result_id, self.mock_session)
        mock_mwv_get_managers.assert_called_with(request=self.mock_request, resource=self.mock_resource)

        self.mock_map_manager.build_geojson_layer.assert_not_called()
        self.mock_map_manager.build_wms_layer.assert_not_called()
        self.mock_map_manager.build_layer_group.assert_not_called()
        mock_log.warning.assert_called()
        self.assertEqual(1, len(self.mock_map_view.layers))
        self.assertEqual(2, len(ret['layer_groups']))

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_plot_for_geojson')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    def test_get_plot_data_geojson(self, mock_get_result, mock_gpfg):
        self.perpare_geojson_layers()
        mock_post = {
            'layer_name': self.layer['layer_name'],
            'feature_id': '1'
        }
        mock_request = mock.MagicMock(POST=mock_post)
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock()
        result_id = '123'
        mock_result = mock.MagicMock(id=result_id)
        mock_result.get_layer.return_value = self.layer
        mock_get_result.return_value = mock_result
        mock_gpfg.return_value = ('Mock Title', ['mock', 'data'], {'mock': 'layout'})

        instance = MapWorkflowResultsView()
        ret = instance.get_plot_data(mock_request, mock_session, mock_resource, result_id)

        mock_get_result.assert_called_with(mock_request, result_id, mock_session)
        mock_result.get_layer.assert_called_with(mock_post['layer_name'])
        mock_gpfg.assert_called_with(self.layer, mock_post['feature_id'])
        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual(b'{"title": "Mock Title", "data": ["mock", "data"], "layout": {"mock": "layout"}}',
                         ret.content)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowView.get_plot_data')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    def test_get_plot_data_wms(self, mock_get_result, mock_mwv_get_plot_data):
        self.prepare_wms_layers()
        mock_post = {
            'layer_name': self.layer['layer_name'],
            'feature_id': '1'
        }
        mock_request = mock.MagicMock(POST=mock_post)
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock()
        result_id = '123'
        mock_result = mock.MagicMock(id=result_id)
        mock_result.get_layer.return_value = self.layer
        mock_get_result.return_value = mock_result
        mock_mwv_get_plot_data.return_value = ('Mock Title', ['mock', 'data'], {'mock': 'layout'})

        instance = MapWorkflowResultsView()
        ret = instance.get_plot_data(mock_request, mock_session, mock_resource, result_id)

        mock_get_result.assert_called_with(mock_request, result_id, mock_session)
        mock_result.get_layer.assert_called_with(mock_post['layer_name'])
        mock_mwv_get_plot_data.assert_called_with(mock_request, mock_session, mock_resource)
        self.assertIsInstance(ret, JsonResponse)
        self.assertEqual(b'{"title": "Mock Title", "data": ["mock", "data"], "layout": {"mock": "layout"}}',
                         ret.content)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView.get_result')  # noqa: E501
    def test_get_plot_data_unsupported(self, mock_get_result):
        self.perpare_geojson_layers()
        self.layer['type'] = 'unsupported-type'  # Change type to arbitrary unsupported type
        mock_post = {
            'layer_name': self.layer['layer_name'],
            'feature_id': '1'
        }
        mock_request = mock.MagicMock(POST=mock_post)
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock()
        result_id = '123'
        mock_result = mock.MagicMock(id=result_id)
        mock_result.get_layer.return_value = self.layer
        mock_get_result.return_value = mock_result

        instance = MapWorkflowResultsView()
        self.assertRaises(TypeError, instance.get_plot_data, mock_request, mock_session, mock_resource, result_id)

        mock_get_result.assert_called_with(mock_request, result_id, mock_session)
        mock_result.get_layer.assert_called_with(mock_post['layer_name'])

    def test_get_plot_for_geojson(self):
        self.perpare_geojson_layers()
        feature_id = '1'
        instance = MapWorkflowResultsView()

        title, data, layout = instance.get_plot_for_geojson(self.layer, feature_id)

        self.assertEqual(self.plot_title, title)
        self.assertListEqual(self.plot_data, data)
        self.assertDictEqual(self.plot_layout, layout)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.log')
    def test_get_plot_for_geojson_invalid_json(self, mock_log):
        self.perpare_geojson_layers()
        # Remove features from geojson
        self.layer['geojson'].pop('features')
        # Add feature back in with wrong key (geometry instead of features)
        self.layer['geojson']['geometry'] = [self.feature]
        feature_id = '1'
        instance = MapWorkflowResultsView()

        title, data, layout = instance.get_plot_for_geojson(self.layer, feature_id)

        self.assertIsNone(title)
        self.assertIsNone(data)
        self.assertIsNone(layout)
        mock_log.warning.assert_called()

    def test_get_plot_for_geojson_id_not_found(self):
        self.perpare_geojson_layers()
        feature_id = '2'
        instance = MapWorkflowResultsView()

        title, data, layout = instance.get_plot_for_geojson(self.layer, feature_id)

        self.assertIsNone(title)
        self.assertIsNone(data)
        self.assertIsNone(layout)

    def test_get_plot_for_geojson_no_plot_in_layer(self):
        self.perpare_geojson_layers(with_plot=False)
        feature_id = '1'
        instance = MapWorkflowResultsView()

        title, data, layout = instance.get_plot_for_geojson(self.layer, feature_id)

        self.assertIsNone(title)
        self.assertIsNone(data)
        self.assertIsNone(layout)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.ResultViewMixin.get_result')
    def test_update_result_layer(self, mock_get_result):
        mock_request = mock.MagicMock()
        mock_request.POST.get.side_effect = ['"foo"', '"color_ramp"']
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock()

        update_layer = {'layer_id': 'foo', 'color_ramp_division_kwargs': {'color_ramp': 'color_ramp'}}
        mock_result = mock.MagicMock()
        mock_result.layers = [update_layer, {'layer_id': 'bar'}]
        mock_get_result.return_value = mock_result

        self.instance.update_result_layer(request=mock_request,
                                          session=mock_session,
                                          resource=mock_resource,
                                          result_id='test_id')

        mock_result.update_layer.assert_called_with(update_layer=update_layer)
