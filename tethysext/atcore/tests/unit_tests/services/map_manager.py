"""
********************************************************************************
* Name: map_manager.py
* Author: nswain
* Created On: September 04, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import copy
import uuid
from unittest import mock
import unittest
from tethys_gizmos.gizmo_options import MVLayer
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class _MapManager(MapManagerBase):

    def compose_map(self, request, *args, **kwargs):
        return None


class MapManagerBaseTests(unittest.TestCase):

    def setUp(self):
        self.spatial_manager = mock.MagicMock(spec=ModelDBSpatialManager)
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

    def test_generate_custom_color_ramp_divisions_decimals(self):
        min_elevation = 100
        max_elevation = 109
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10
        )
        expected = {
            'val1': '100.00000',
            'val2': '101.00000',
            'val3': '102.00000',
            'val4': '103.00000',
            'val5': '104.00000',
            'val6': '105.00000',
            'val7': '106.00000',
            'val8': '107.00000',
            'val9': '108.00000',
            'val10': '109.00000'
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

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.get_vector_style_map')
    def test_build_geojson_layer(self, mock_gvsm, mock_bvl):
        geojson = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [-87.89832948468124, 30.651451015987234]},
                    'properties': {'id': 4}
                 },
            ]
        }

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_geojson_layer(
            geojson=geojson,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable
        )

        expected_options = copy.deepcopy(geojson)
        expected_options['features'][0]['properties']['layer_name'] = layer_name

        mock_bvl.assert_called_once()
        mock_gvsm.assert_called_once()
        mock_bvl.assert_called_with(
            layer_id='',
            layer_name=layer_name,
            layer_source='GeoJSON',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            style_map=mock_gvsm()
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.get_vector_style_map')
    def test_build_geojson_layer_all_pass_through_args(self, mock_gvsm, mock_bvl):
        geojson = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [-87.89832948468124, 30.651451015987234]},
                    'properties': {'id': 4}
                },
            ]
        }

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_geojson_layer(
            geojson=geojson,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            layer_id='LAYER_ID_PASS_THROUGH',
            extent=[1, 2, 3, 4],
            visible=False,
            public=False,
            selectable=True,
            plottable=True,
            has_action=False,
            popup_title='POPUP_TITLE_PASS_THROUGH',
            excluded_properties=[1, 2, 3]
        )

        expected_options = copy.deepcopy(geojson)
        expected_options['features'][0]['properties']['layer_name'] = layer_name

        mock_bvl.assert_called_once()
        mock_gvsm.assert_called_once()
        mock_bvl.assert_called_with(
            layer_name=layer_name,
            layer_source='GeoJSON',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=[1, 2, 3, 4],
            layer_id='LAYER_ID_PASS_THROUGH',
            visible=False,
            public=False,
            selectable=True,
            plottable=True,
            has_action=False,
            popup_title='POPUP_TITLE_PASS_THROUGH',
            excluded_properties=[1, 2, 3],
            style_map=mock_gvsm()
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    def test_build_wms_layer(self, mock_bvl):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0'
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous',
            'tileGrid': map_manager.DEFAULT_TILE_GRID
        }

        mock_bvl.assert_called_once()
        mock_bvl.assert_called_with(
            layer_id='',
            layer_name=layer_name,
            layer_source='TileWMS',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            geometry_attribute='geometry'
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    def test_build_wms_layer_all_pass_through_args(self, mock_bvl):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            visible=False,
            selectable=True,
            plottable=True,
            has_action=False,
            extent=[1, 2, 3, 4],
            public=False,
            geometry_attribute='GEOM_ATTR_PASS_THROUGH',
            layer_id='LAYER_ID_PASS_THROUGH',
            excluded_properties=[1, 2, 3],
            popup_title='POPUP_TITLE_PASS_THROUGH'
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0'
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous',
            'tileGrid': map_manager.DEFAULT_TILE_GRID
        }

        mock_bvl.assert_called_once()
        mock_bvl.assert_called_with(
            layer_name=layer_name,
            layer_source='TileWMS',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            visible=False,
            selectable=True,
            plottable=True,
            has_action=False,
            extent=[1, 2, 3, 4],
            public=False,
            geometry_attribute='GEOM_ATTR_PASS_THROUGH',
            layer_id='LAYER_ID_PASS_THROUGH',
            excluded_properties=[1, 2, 3],
            popup_title='POPUP_TITLE_PASS_THROUGH'
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    def test_build_wms_layer_not_tiled(self, mock_bvl):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            tiled=False
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous'
        }

        mock_bvl.assert_called_once()
        mock_bvl.called_with(
            layer_id='',
            layer_name=layer_name,
            layer_source='ImageWMS',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            geometry_attribute='geometry'
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    def test_build_wms_layer_viewparams(self, mock_bvl):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        viewparams = 'foo:bar;baz:jar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            viewparams=viewparams
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0',
                'VIEWPARAMS': viewparams
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous',
            'tileGrid': map_manager.DEFAULT_TILE_GRID
        }

        mock_bvl.assert_called_once()
        mock_bvl.called_with(
            layer_id='',
            layer_name=layer_name,
            layer_source='TileWMS',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            geometry_attribute='geometry'
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    def test_build_wms_layer_env(self, mock_bvl):
        endpoint = 'http://www.example.com/geoserver/wms'
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        env = 'foo:bar;baz:jar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            env=env
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0',
                'ENV': env
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous',
            'tileGrid': map_manager.DEFAULT_TILE_GRID
        }

        mock_bvl.assert_called_once()
        mock_bvl.called_with(
            layer_id='',
            layer_name=layer_name,
            layer_source='TileWMS',
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=expected_options,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            geometry_attribute='geometry'
        )

        # IMPORTANT: Test this AFTER assert_called_with
        self.assertEqual(ret, mock_bvl())

    def test_build_mv_layer(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
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

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_popup_title(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        popup_title = 'Baz'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                popup_title='Baz'
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': popup_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_excluded_properties(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]
        excluded_properties = ['id', 'foo', 'bar', 'baz']

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                excluded_properties=excluded_properties
            )

        opts = ret['options']
        expected_data = {
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True,
            'excluded_properties': ['id', 'type', 'layer_name', 'foo', 'bar', 'baz']
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_plottable(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
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

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                plottable=True
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True,
            'plottable': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_has_action(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
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

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                has_action=True
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True,
            'has_action': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_extent(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]
        custom_extent = [1, 2, 3, 4]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                extent=custom_extent
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(custom_extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_style_map(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        extent = [400, 300, 800, 100]
        style_map = {
            'Point': {'ol.style.Style': {
                'image': {'ol.style.Circle': {
                    'radius': 5,
                    'fill': {'ol.style.Fill': {
                        'color': 'red',
                    }},
                    'stroke': {'ol.style.Stroke': {
                        'color': 'blue',
                    }}
                }}
            }},
        }

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                style_map=style_map
            )

        opts = ret['options']

        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        expected_layer_options = {
            'visible': True,
            'style_map': style_map
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual(expected_layer_options, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_not_visible(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
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

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                visible=False
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': False}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    @mock.patch('tethys_gizmos.gizmo_options.map_view.log')  # mock out geometry attribute warning
    def test_build_mv_layer_selectable(self, _):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
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

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                selectable=True
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(True, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_layer_id(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        layer_id = uuid.uuid4()
        layer_id_str = str(layer_id)
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                model_db=self.model_db
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                layer_id=layer_id
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_id': layer_id_str,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_vector_style_map(self):
        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            model_db=self.model_db
        )

        ret = map_manager.get_vector_style_map()

        self.assertIsInstance(ret, dict)
        self.assertIn('Point', ret.keys())
        self.assertIn('LineString', ret.keys())
        self.assertIn('Polygon', ret.keys())

    def test_get_plot_for_layer_feature(self):
        ret = self.map_manager.get_plot_for_layer_feature(layer_name='layer1', feature_id='F001')
        self.assertEqual('F001', ret[1][0]['name'])
        self.assertEqual('layer1', ret[2]['xaxis']['title'])
