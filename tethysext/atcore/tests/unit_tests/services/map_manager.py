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
from collections import OrderedDict
from unittest import mock
import unittest
from tethys_gizmos.gizmo_options import MVLayer
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class _MapManager(MapManagerBase):

    def compose_map(self, request, *args, **kwargs):
        return None


class MapManagerBaseTests(unittest.TestCase):

    def setUp(self):
        self.spatial_manager = mock.MagicMock(spec=ModelDBSpatialManager)
        self.resource = mock.MagicMock(spec=Resource)
        self.map_manager = _MapManager(self.spatial_manager, self.resource)

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
            extent=[-10, -10, 10, 10],
            zoom=MapManagerBase.DEFAULT_ZOOM,
            maxZoom=MapManagerBase.MAX_ZOOM,
            minZoom=MapManagerBase.MIN_ZOOM
        )

        self.spatial_manager.get_extent_for_project.assert_called()

        self.assertEqual(mock_mvv(), view)
        self.assertEqual(test_extent, extent)

    @mock.patch('tethysext.atcore.services.map_manager.MVView')
    def test_get_map_extent_no_extent(self, mock_mvv):
        self.spatial_manager.get_extent_for_project.return_value = None
        view, extent = self.map_manager.get_map_extent()

        mock_mvv.assert_called_with(
            projection='EPSG:4326',
            extent=None,
            zoom=MapManagerBase.DEFAULT_ZOOM,
            maxZoom=MapManagerBase.MAX_ZOOM,
            minZoom=MapManagerBase.MIN_ZOOM
        )

        self.spatial_manager.get_extent_for_project.assert_called()

        self.assertEqual(mock_mvv(), view)
        self.assertIsNone(extent)

    def test_generate_custom_color_ramp_divisions(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            value_precision=1,
            num_divisions=10
        )
        expected = {
            'val1': '100.0', 'color1': '#fff100',
            'val2': '200.0', 'color2': '#ff8c00',
            'val3': '300.0', 'color3': '#e81123',
            'val4': '400.0', 'color4': '#ec008c',
            'val5': '500.0', 'color5': '#68217a',
            'val6': '600.0', 'color6': '#00188f',
            'val7': '700.0', 'color7': '#00bcf2',
            'val8': '800.0', 'color8': '#00b294',
            'val9': '900.0', 'color9': '#009e49',
            'val10': '1000.0', 'color10': '#bad80a'
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_val_no_data(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            value_precision=1,
            no_data_value=0,
        )
        expected = {
            'val1': '100.0', 'color1': '#fff100',
            'val2': '200.0', 'color2': '#ff8c00',
            'val3': '300.0', 'color3': '#e81123',
            'val4': '400.0', 'color4': '#ec008c',
            'val5': '500.0', 'color5': '#68217a',
            'val6': '600.0', 'color6': '#00188f',
            'val7': '700.0', 'color7': '#00bcf2',
            'val8': '800.0', 'color8': '#00b294',
            'val9': '900.0', 'color9': '#009e49',
            'val10': '1000.0', 'color10': '#bad80a',
            'val_no_data': 0}
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_with_colors(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            color_ramp="Blue and Red"
        )
        expected = {
            'val1': '100.00', 'color1': '#a50026',
            'val2': '200.00', 'color2': '#d73027',
            'val3': '300.00', 'color3': '#f46d43',
            'val4': '400.00', 'color4': '#fdae61',
            'val5': '500.00', 'color5': '#fee090',
            'val6': '600.00', 'color6': '#e0f3f8',
            'val7': '700.00', 'color7': '#abd9e9',
            'val8': '800.00', 'color8': '#74add1',
            'val9': '900.00', 'color9': '#4575b4',
            'val10': '1000.00', 'color10': '#313695'
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_first_division(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            value_precision=1,
            first_division=0
        )
        expected = {
            'val0': '100.0', 'color0': '#fff100',
            'val1': '200.0', 'color1': '#ff8c00',
            'val2': '300.0', 'color2': '#e81123',
            'val3': '400.0', 'color3': '#ec008c',
            'val4': '500.0', 'color4': '#68217a',
            'val5': '600.0', 'color5': '#00188f',
            'val6': '700.0', 'color6': '#00bcf2',
            'val7': '800.0', 'color7': '#00b294',
            'val8': '900.0', 'color8': '#009e49',
            'val9': '1000.0', 'color9': '#bad80a'
        }

        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_prefix(self):
        min_elevation = 100
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            value_precision=1,
            prefix='foo'
        )
        expected = {
            'foo1': '100.0', 'color1': '#fff100',
            'foo2': '200.0', 'color2': '#ff8c00',
            'foo3': '300.0', 'color3': '#e81123',
            'foo4': '400.0', 'color4': '#ec008c',
            'foo5': '500.0', 'color5': '#68217a',
            'foo6': '600.0', 'color6': '#00188f',
            'foo7': '700.0', 'color7': '#00bcf2',
            'foo8': '800.0', 'color8': '#00b294',
            'foo9': '900.0', 'color9': '#009e49',
            'foo10': '1000.0', 'color10': '#bad80a'
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_top_offset(self):
        min_elevation = 10
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            value_precision=1,
            top_offset=900
        )
        expected = {
            'val1': '10.0', 'color1': '#fff100',
            'val2': '20.0', 'color2': '#ff8c00',
            'val3': '30.0', 'color3': '#e81123',
            'val4': '40.0', 'color4': '#ec008c',
            'val5': '50.0', 'color5': '#68217a',
            'val6': '60.0', 'color6': '#00188f',
            'val7': '70.0', 'color7': '#00bcf2',
            'val8': '80.0', 'color8': '#00b294',
            'val9': '90.0', 'color9': '#009e49',
            'val10': '100.0', 'color10': '#bad80a'
        }
        self.assertEqual(expected, val)

    def test_generate_custom_color_ramp_divisions_bottom_offset(self):
        min_elevation = 10
        max_elevation = 1000
        val = self.map_manager.generate_custom_color_ramp_divisions(
            min_value=min_elevation,
            max_value=max_elevation,
            num_divisions=10,
            value_precision=1,
            bottom_offset=900
        )

        expected = {
            'val1': '910.0', 'color1': '#fff100',
            'val2': '920.0', 'color2': '#ff8c00',
            'val3': '930.0', 'color3': '#e81123',
            'val4': '940.0', 'color4': '#ec008c',
            'val5': '950.0', 'color5': '#68217a',
            'val6': '960.0', 'color6': '#00188f',
            'val7': '970.0', 'color7': '#00bcf2',
            'val8': '980.0', 'color8': '#00b294',
            'val9': '990.0', 'color9': '#009e49',
            'val10': '1000.0', 'color10': '#bad80a'
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

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.get_vector_style_map')
    def test_build_cesium_layer_invalid(self, _):
        model = [{'model': {'uri': 'glb_file.glb', 'show': True, 'shadows': 'enabled'},
                  'name': 'Funwave',
                  'orientation': {
                      'Cesium.Transforms.headingPitchRollQuaternion':
                          [{'Cesium.Cartesian3.fromDegrees': [-95.245, 28.9341, -31]},
                           {'Cesium.HeadingPitchRoll': [{'Cesium.Math.toRadians': -42}, 0, 0]}]},
                  'position': {'Cesium.Cartesian3.fromDegrees': [-95.245, 28.9341, -31]},
                  },
                 ]

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        self.assertRaises(ValueError, self.map_manager.build_cesium_layer, cesium_type='WrongType', cesium_json=model,
                          layer_name=layer_name, layer_title=layer_title, layer_variable=layer_variable)

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase._build_mv_layer')
    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.get_vector_style_map')
    def test_build_cesium_layer_model(self, mock_gvsm, mock_bvl):
        model = [{'model': {'uri': 'glb_file.glb', 'show': True, 'shadows': 'enabled'},
                  'name': 'Funwave',
                  'orientation': {
                      'Cesium.Transforms.headingPitchRollQuaternion':
                          [{'Cesium.Cartesian3.fromDegrees': [-95.245, 28.9341, -31]},
                           {'Cesium.HeadingPitchRoll': [{'Cesium.Math.toRadians': -42}, 0, 0]}]},
                  'position': {'Cesium.Cartesian3.fromDegrees': [-95.245, 28.9341, -31]},
                  },
                 ]

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
        )

        ret = map_manager.build_cesium_layer(
            cesium_type='CesiumModel',
            cesium_json=model,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable
        )

        mock_bvl.assert_called_once()
        mock_gvsm.assert_called_once()
        mock_bvl.assert_called_with(
            layer_source='CesiumModel',
            layer_id='',
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=model,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            show_download=False,
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
    def test_build_cesium_layer_primitive(self, mock_gvsm, mock_bvl):
        primitive = [{'Cesium.Cesium3DTileset': {'url': {'Cesium.IonResource.fromAssetId': 512295}}}]

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
        )

        ret = map_manager.build_cesium_layer(
            cesium_type='CesiumPrimitive',
            cesium_json=primitive,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable
        )

        mock_bvl.assert_called_once()
        mock_gvsm.assert_called_once()
        mock_bvl.assert_called_with(
            layer_source='CesiumPrimitive',
            layer_id='',
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=primitive,
            extent=None,
            visible=True,
            public=True,
            selectable=False,
            show_download=False,
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
            resource=self.resource
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
            show_download=False,
            plottable=False,
            has_action=False,
            popup_title=None,
            excluded_properties=None,
            style_map=mock_gvsm(),
            label_options=None,
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
                    'properties': {'id': 4},
                    'label': 'baz',
                },
            ]
        }

        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
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
            excluded_properties=[1, 2, 3],
            label_options={'label_property': 'baz'},
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
            show_download=False,
            plottable=True,
            has_action=False,
            popup_title='POPUP_TITLE_PASS_THROUGH',
            excluded_properties=[1, 2, 3],
            label_options={'label_property': 'baz'},
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
            resource=self.resource
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
            geometry_attribute='geometry',
            times=None,
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
            resource=self.resource
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
            popup_title='POPUP_TITLE_PASS_THROUGH',
            times=None,
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
            resource=self.resource
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            color_ramp_division_kwargs={'min_value': 1, 'max_value': 10, 'color_ramp': 'Blue and Red'},
            tiled=False
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'ENV': ('val1:1.00;color1:#a50026;val2:2.00;color2:#d73027;val3:3.00;color3:#f46d43;'
                        'val4:4.00;color4:#fdae61;val5:5.00;color5:#fee090;val6:6.00;color6:#e0f3f8;'
                        'val7:7.00;color7:#abd9e9;val8:8.00;color8:#74add1;val9:9.00;color9:#4575b4;'
                        'val10:10.00;color10:#313695'),
            },
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous'
        }

        mock_bvl.assert_called_once()
        mock_bvl.assert_called_with(
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
            geometry_attribute='geometry',
            times=None
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
            resource=self.resource
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            color_ramp_division_kwargs={'min_value': 1, 'max_value': 10, 'color_ramp': 'Blue and Red'},
            viewparams=viewparams
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0',
                'VIEWPARAMS': viewparams,
                'ENV': ('val1:1.00;color1:#a50026;val2:2.00;color2:#d73027;val3:3.00;color3:#f46d43;'
                        'val4:4.00;color4:#fdae61;val5:5.00;color5:#fee090;val6:6.00;color6:#e0f3f8;'
                        'val7:7.00;color7:#abd9e9;val8:8.00;color8:#74add1;val9:9.00;color9:#4575b4;'
                        'val10:10.00;color10:#313695'),
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
            geometry_attribute='geometry',
            times=None
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
            resource=self.resource
        )

        ret = map_manager.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            color_ramp_division_kwargs={'min_value': 1, 'max_value': 10, 'color_ramp': 'Blue and Red'},
            env=env
        )

        expected_options = {
            'url': endpoint,
            'params': {
                'LAYERS': layer_name,
                'TILED': True,
                'TILESORIGIN': '0.0,0.0',
                'ENV': env + (';val1:1.00;color1:#a50026;val2:2.00;color2:#d73027;val3:3.00;color3:#f46d43;'
                              'val4:4.00;color4:#fdae61;val5:5.00;color5:#fee090;val6:6.00;color6:#e0f3f8;'
                              'val7:7.00;color7:#abd9e9;val8:8.00;color8:#74add1;val9:9.00;color9:#4575b4;'
                              'val10:10.00;color10:#313695'),
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
            geometry_attribute='geometry',
            times=None
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
            'excluded_properties': ['id', 'type', 'layer_name', 'plot'],
            'layer_id': layer_name,
            'layer_name': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True,
            'plottable': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertDictEqual(expected_data, ret['data'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
            'show_download': False,
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
                resource=self.resource
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
        self.assertEqual({'visible': False, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
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
                resource=self.resource
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
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)

    def test_build_mv_layer_w_geometry_attributes(self):
        layer_source = 'GeoJSON'
        given_options = {'type': 'FeatureCollection', 'features': []}
        layer_name = 'foo'
        layer_title = 'Foo'
        layer_variable = 'Bar'
        geometry_attribute = 'geometry'
        extent = [400, 300, 800, 100]

        with mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = extent
            map_manager = _MapManager(
                spatial_manager=self.spatial_manager,
                resource=self.resource
            )

            ret = map_manager._build_mv_layer(
                layer_source=layer_source,
                layer_name=layer_name,
                layer_title=layer_title,
                layer_variable=layer_variable,
                options=given_options,
                geometry_attribute=geometry_attribute
            )

        opts = ret['options']
        expected_data = {
            'excluded_properties': ['id', 'type', 'layer_name'],
            'layer_name': layer_name,
            'layer_id': layer_name,
            'popup_title': layer_title,
            'layer_variable': layer_variable,
            'toggle_status': True
        }

        self.assertIsInstance(ret, MVLayer)
        self.assertEqual(layer_source, ret['source'])
        self.assertEqual({'visible': True, 'show_download': False}, ret['layer_options'])
        self.assertEqual(layer_title, ret['legend_title'])
        self.assertEqual(extent, ret['legend_extent'])
        self.assertEqual(False, ret['feature_selection'])
        self.assertEqual(expected_data, ret['data'])
        self.assertEqual(given_options, opts)
        self.assertEqual(geometry_attribute, ret['geometry_attribute'])

    def test_vector_style_map(self):
        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
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

    @mock.patch.dict('tethysext.atcore.services.map_manager.MapManagerBase.COLOR_RAMPS', values={'Default': ''}, clear=True)  # noqa: E501
    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.generate_custom_color_ramp_divisions')
    def test_build_legend(self, mock_gccrd):
        mock_gccrd.return_value = {'val1': '100', 'val2': '200', 'color1': '#fff100', 'color2': '#ff8c00'}
        mock_COLOR_RAMPS = {'Default': ''}
        mock_crd_kwargs = {'min_value': 100, 'max_value': 200, 'num_divisions': 2}
        mock_layer = {
            'layer_name': 'test:layer_name', 'layer_title': 'Test_Title', 'layer_variable': 'test:layer_variable',
            'layer_id': '', 'viewparams': None, 'env': None, 'color_ramp_division_kwargs': mock_crd_kwargs
        }

        expected = {
            'legend_id': 'test_layer_variable',
            'title': 'Test Title',
            'divisions': OrderedDict([(100.0, '#fff100'), (200.0, '#ff8c00')]),
            'color_list': mock_COLOR_RAMPS.keys(),
            'layer_id': 'test:layer_name',
            'min_value': 100,
            'max_value': 200,
            'color_ramp': 'Default',
            'prefix': 'val',
            'color_prefix': 'color',
            'first_division': 1,
            'units': 'Ft',
        }

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
        )

        ret = map_manager.build_legend(mock_layer, units='Ft')
        self.assertEqual(ret, expected)

    @mock.patch.dict('tethysext.atcore.services.map_manager.MapManagerBase.COLOR_RAMPS', values={'Default': ''}, clear=True)  # noqa: E501
    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.generate_custom_color_ramp_divisions')
    def test_build_legend_with_color_ramp(self, mock_gccrd):
        mock_gccrd.return_value = {'val1': '100', 'val2': '200', 'color1': '#fff100', 'color2': '#ff8c00'}
        mock_COLOR_RAMPS = {'Default': ''}
        mock_crd_kwargs = {'min_value': 100, 'max_value': 200, 'num_divisions': 2, 'color_ramp': 'Default'}
        mock_layer = {
            'layer_name': 'test:layer_name', 'layer_title': 'Test_Title', 'layer_variable': 'test:layer_variable',
            'layer_id': '', 'viewparams': None, 'env': None, 'color_ramp_division_kwargs': mock_crd_kwargs
        }

        expected = {
            'legend_id': 'test_layer_variable',
            'title': 'Test Title',
            'divisions': OrderedDict([(100.0, '#fff100'), (200.0, '#ff8c00')]),
            'color_list': mock_COLOR_RAMPS.keys(),
            'layer_id': 'test:layer_name',
            'min_value': 100,
            'max_value': 200,
            'color_ramp': 'Default',
            'prefix': 'val',
            'color_prefix': 'color',
            'first_division': 1,
            'units': 'Ft',
        }

        map_manager = _MapManager(
            spatial_manager=self.spatial_manager,
            resource=self.resource
        )

        ret = map_manager.build_legend(mock_layer, units='Ft')
        self.assertEqual(ret, expected)
