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
from tethysext.atcore.services.map_manager import MapManagerBase


class _MapManager(MapManagerBase):

    def compose_map(self, request, *args, **kwargs):
        return None


class MapManagerBaseTests(unittest.TestCase):

    def setUp(self):
        self.spatial_manager = mock.MagicMock()
        self.model_db = mock.MagicMock()
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
