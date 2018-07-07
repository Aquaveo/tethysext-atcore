"""
********************************************************************************
* Name: spatial_manager.py
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
from tethysext.atcore.services.spatial_manager import SpatialManager


class SpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_ows_endpoint(self, _):
        spatial_manger = SpatialManager(self.geoserver_engine)
        spatial_manger.get_ows_endpoint()
        spatial_manger.gs_api.get_ows_endpoint.assert_called_with(SpatialManager.WORKSPACE, True)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_wms_endpoint(self, _):
        spatial_manger = SpatialManager(self.geoserver_engine)
        spatial_manger.get_wms_endpoint()
        spatial_manger.gs_api.get_wms_endpoint.assert_called_with(SpatialManager.WORKSPACE, True)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_link_geoserver_to_db(self, _):
        pass

    def test_link_geoserver_to_db_with_out_reload_config(self):
        pass

    def test_unlink_geoserver_from_db(self):
        pass

    def test_create_workspace(self):
        pass

    def test_get_db_specific_store_id(selfs):
        pass

    def test_reload(self):
        pass
