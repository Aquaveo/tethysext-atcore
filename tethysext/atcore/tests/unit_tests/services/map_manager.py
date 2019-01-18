"""
********************************************************************************
* Name: map_manager.py
* Author: nswain
* Created On: September 04, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
from tethys_gizmos.gizmo_options import MVLayer
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.spatial_manager import SpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class _MapManager(MapManagerBase):

    def compose_map(self, request, *args, **kwargs):
        return None


class MapManagerBaseTests(unittest.TestCase):

    def setUp(self):
        self.spatial_manager = mock.MagicMock(spec=SpatialManager)
        self.model_db = mock.MagicMock(spec=ModelDatabase)
        self.map_manager = _MapManager(self.spatial_manager, self.model_db)

    def tearDown(self):
        pass

    def test_map_extent_property(self):
        self.map_manager.get_map_extent = mock.MagicMock(
            return_value=('test_view', 'test_extent')
        )
        ret = self.map_manager.map_extent
        self.map_manager.get_map_extent.assert_called()
        self.assertEqual('test_extent', ret)

    def test_map_extent_property_cached(self):
        self.map_manager.get_map_extent = mock.MagicMock(
            return_value=('test_view', 'test_extent')
        )
        self.map_manager._map_extent = 'bar'
        ret = self.map_manager.map_extent
        self.map_manager.get_map_extent.assert_not_called()
        self.assertEqual('bar', ret)

    def test_default_view_property(self):
        self.map_manager.get_map_extent = mock.MagicMock(
            return_value=('test_view', 'test_extent')
        )
        ret = self.map_manager.default_view
        self.map_manager.get_map_extent.assert_called()
        self.assertEqual('test_view', ret)

    def test_default_view_property_cached(self):
        self.map_manager.get_map_extent = mock.MagicMock(
            return_value=('test_view', 'test_extent')
        )
        self.map_manager._default_view = 'foo'
        ret = self.map_manager.default_view
        self.map_manager.get_map_extent.assert_not_called()
        self.assertEqual('foo', ret)

    def test_build_layer_group(self):
        ret = self.map_manager.build_layer_group(id='ID001', display_name='Foo', layers='Layer1')
        self.assertEqual('Foo', ret['display_name'])
        self.assertEqual('ID001', ret['id'])
        self.assertEqual('checkbox', ret['control'])
        self.assertEqual('Layer1', ret['layers'])
        self.assertTrue(ret['visible'])

    def test_build_layer_group_value_error(self):
        self.assertRaises(ValueError, self.map_manager.build_layer_group,
                          id='ID001', display_name='Foo', layers='Layer1', layer_control='groupbox')

    def test_get_wms_endpoint(self):
        ret = self.map_manager.get_wms_endpoint()
        self.spatial_manager.get_wms_endpoint.assert_called_with(public=True)
        self.assertEqual(self.spatial_manager.get_wms_endpoint(), ret)

    @mock.patch('tethysext.atcore.services.map_manager.MVView')
    def test_get_map_extent(self, mock_mvv):
        test_extent = [-10, -10, 10, 10]
        self.spatial_manager.get_extent_for_project.return_value = test_extent

        view, extent = self.map_manager.get_map_extent()

        mock_mvv.assert_called_with(
            projection='EPSG:4326',
            center=[0.0, 0.0],
            zoom=MapManagerBase.DEFAULT_ZOOM,
            maxZoom=MapManagerBase.MAX_ZOOM,
            minZoom=MapManagerBase.MIN_ZOOM
        )

        self.spatial_manager.get_extent_for_project.assert_called_with(
            model_db=self.model_db
        )

        self.assertEqual(mock_mvv(), view)
        self.assertEqual(test_extent, extent)

    @mock.patch('tethysext.atcore.services.map_manager.MVView')
    def test_get_map_extent_no_extent(self, mock_mvv):
        self.spatial_manager.get_extent_for_project.return_value = None
        view, extent = self.map_manager.get_map_extent()

        mock_mvv.assert_called_with(
            projection='EPSG:4326',
            center=MapManagerBase.DEFAULT_CENTER,
            zoom=MapManagerBase.DEFAULT_ZOOM,
            maxZoom=MapManagerBase.MAX_ZOOM,
            minZoom=MapManagerBase.MIN_ZOOM
        )

        self.spatial_manager.get_extent_for_project.assert_called_with(
            model_db=self.model_db
        )

        self.assertEqual(mock_mvv(), view)
        self.assertIsNone(extent)

    def test_generate_custom_color_ramp_divisions(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10
        )
        expected = {
            'val1': 100.0,
            'val2': 200.0,
            'val3': 300.0,
            'val4': 400.0,
            'val5': 500.0,
            'val6': 600.0,
            'val7': 700.0,
            'val8': 800.0,
            'val9': 900.0,
            'val10': 1000.0
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_first_division(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            first_division=0
        )
        expected = {
            'val0': 100.0,
            'val1': 200.0,
            'val2': 300.0,
            'val3': 400.0,
            'val4': 500.0,
            'val5': 600.0,
            'val6': 700.0,
            'val7': 800.0,
            'val8': 900.0,
            'val9': 1000.0
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_prefix(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            prefix='foo'
        )
        expected = {
            'foo1': 100.0,
            'foo2': 200.0,
            'foo3': 300.0,
            'foo4': 400.0,
            'foo5': 500.0,
            'foo6': 600.0,
            'foo7': 700.0,
            'foo8': 800.0,
            'foo9': 900.0,
            'foo10': 1000.0
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_top_offset(self):
        min_elevation = 10
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            top_offset=900
        )
        expected = {
            'val1': 10.0,
            'val2': 20.0,
            'val3': 30.0,
            'val4': 40.0,
            'val5': 50.0,
            'val6': 60.0,
            'val7': 70.0,
            'val8': 80.0,
            'val9': 90.0,
            'val10': 100.0
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_bottom_offset(self):
        min_elevation = 10
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            bottom_offset=900
        )

        expected = {
            'val1': 910.0,
            'val2': 920.0,
            'val3': 930.0,
            'val4': 940.0,
            'val5': 950.0,
            'val6': 960.0,
            'val7': 970.0,
            'val8': 980.0,
            'val9': 990.0,
            'val10': 1000.0
        }
        self.assertEqual(expected, val)

    def test_build_param_string_multiple_kwargs(self):
        ret = self.map_manager.build_param_string(foo='bar', baz='jar')
        parts = ret.split(';')
        self.assertIn('baz:jar', parts)
        self.assertIn('foo:bar', parts)

    def test_build_param_string_single_kwargs(self):
        ret = self.map_manager.build_param_string(foo='bar')
        self.assertEqual('foo:bar', ret)

    def test_build_param_string_no_kwargs(self):
        ret = self.map_manager.build_param_string()
        self.assertEqual('', ret)

    def test_build_mv_layer(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable
            )

        opts = ret['options']
        params = opts['params']
        data = ret['data']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('TileWMS', ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertIn('tileGrid', opts)
        self.assertEqual(map_manager.DEFAULT_TILE_GRID, opts['tileGrid'])
        self.assertIn('TILED', params)
        self.assertTrue(params['TILED'])
        self.assertIn('TILESORIGIN', params)
        self.assertEqual('0.0,0.0', params['TILESORIGIN'])
        self.assertIn('layer_name', data)
        self.assertEqual(layer_name, data['layer_name'])
        self.assertIn('layer_variable', data)
        self.assertEqual(layer_variable, data['layer_variable'])

    def test_build_mv_layer_not_tiled(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                tiled=False
            )

        opts = ret['options']
        params = opts['params']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('ImageWMS', ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertNotIn('tileGrid', opts)
        self.assertNotIn('TILED', params)
        self.assertNotIn('TILESORIGIN', params)

    def test_build_mv_layer_viewparams(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]
        viewparams = 'foo:bar;baz:jar'

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                viewparams=viewparams
            )

        opts = ret['options']
        params = opts['params']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('TileWMS', ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertIn('tileGrid', opts)
        self.assertEqual(map_manager.DEFAULT_TILE_GRID, opts['tileGrid'])
        self.assertIn('TILED', params)
        self.assertTrue(params['TILED'])
        self.assertIn('TILESORIGIN', params)
        self.assertEqual('0.0,0.0', params['TILESORIGIN'])
        self.assertIn('VIEWPARAMS', params)
        self.assertEqual(viewparams, params['VIEWPARAMS'])

    def test_build_mv_layer_env(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]
        env = 'foo:bar;baz:jar'

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                env=env
            )

        opts = ret['options']
        params = opts['params']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('TileWMS', ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertIn('tileGrid', opts)
        self.assertEqual(map_manager.DEFAULT_TILE_GRID, opts['tileGrid'])
        self.assertIn('TILED', params)
        self.assertTrue(params['TILED'])
        self.assertIn('TILESORIGIN', params)
        self.assertEqual('0.0,0.0', params['TILESORIGIN'])
        self.assertIn('ENV', params)
        self.assertEqual(env, params['ENV'])

    def test_build_mv_layer_not_visible(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                visible=False
            )

        opts = ret['options']
        params = opts['params']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('TileWMS', ret['source'])
        self.assertEqual({'visible': False}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertIn('tileGrid', opts)
        self.assertEqual(map_manager.DEFAULT_TILE_GRID, opts['tileGrid'])
        self.assertIn('TILED', params)
        self.assertTrue(params['TILED'])
        self.assertIn('TILESORIGIN', params)
        self.assertEqual('0.0,0.0', params['TILESORIGIN'])

    def test_build_mv_layer_plottable(self):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        plottable = True
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager.build_mv_layer(
                endpoint=endpoint,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                plottable=plottable
            )

        opts = ret['options']
        params = opts['params']
        data = ret['data']

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual('TileWMS', ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(endpoint, opts['url'])
        self.assertEqual('geoserver', opts['serverType'])
        self.assertEqual(layer_name, params['LAYERS'])
        self.assertIn('tileGrid', opts)
        self.assertEqual(map_manager.DEFAULT_TILE_GRID, opts['tileGrid'])
        self.assertIn('TILED', params)
        self.assertTrue(params['TILED'])
        self.assertIn('TILESORIGIN', params)
        self.assertEqual('0.0,0.0', params['TILESORIGIN'])
        self.assertIn('layer_name', data)
        self.assertEqual(layer_name, data['layer_name'])
        self.assertIn('layer_variable', data)
        self.assertEqual(layer_variable, data['layer_variable'])
        self.assertTrue(plottable, data['plottable'])

    def test_get_plot_for_layer_feature(self):
        ret = self.map_manager.get_plot_for_layer_feature(layer_name='layer1', feature_id='F001')
        self.assertEqual('F001', ret[1][0]['name'])
        self.assertEqual('layer1', ret[2]['xaxis']['title'])
