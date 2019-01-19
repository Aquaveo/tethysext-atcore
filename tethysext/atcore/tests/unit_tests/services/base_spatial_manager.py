"""
********************************************************************************
* Name: model_db_spatial_manager.py
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager, reload_config


class _BaseSpatialManager(BaseSpatialManager):

    @reload_config()
    def test_decorator(self, reload_config=True):
        return reload_config

    def get_extent_for_project(self, model_db):
        return [-1, 1, -1, 1]


class BaseSpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()

    def tearDown(self):
        pass

    def test_get_extent_for_project(self):
        spatial_manager = BaseSpatialManager(self.geoserver_engine)
        spatial_manager.get_extent_for_project()

    def test_get_projection_units(self):
        spatial_manager = BaseSpatialManager(self.geoserver_engine)
        spatial_manager.get_projection_units()

    def test_get_projection_string(self):
        spatial_manager = BaseSpatialManager(self.geoserver_engine)
        spatial_manager.get_projection_string()

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_reload_config_decorator(self, _):
        foo = _BaseSpatialManager(self.geoserver_engine)
        ret = foo.test_decorator()
        self.assertTrue(ret)
        foo.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_reload_config_decorator_no_reload_config(self, _):
        foo = _BaseSpatialManager(self.geoserver_engine)
        ret = foo.test_decorator(reload_config=False)
        self.assertFalse(ret)
        foo.gs_api.reload.assert_not_called()

    def test_reload_config_decorator_non_method(self):
        @reload_config()
        def not_a_method(number, string):
            pass

        self.assertRaises(ValueError, not_a_method, 1, 'foo')

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_create_workspace(self, _):
        spatial_manager = _BaseSpatialManager(self.geoserver_engine)
        spatial_manager.create_workspace()
        self.geoserver_engine.create_workspace.assert_called_with(BaseSpatialManager.WORKSPACE, BaseSpatialManager.URI)
        spatial_manager.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_get_db_specific_store_id(self, _):
        spatial_manager = _BaseSpatialManager(self.geoserver_engine)
        mock_modeldatabase = mock.MagicMock()
        mock_modeldatabase.get_id.return_value = 'I001'
        expected_Result = spatial_manager.get_db_specific_store_id(mock_modeldatabase)
        self.assertEqual('{}:{}'.format(BaseSpatialManager.WORKSPACE, 'I001'), expected_Result)

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_get_ows_endpoint(self, _):
        model_db_spatial_manager = _BaseSpatialManager(self.geoserver_engine)
        model_db_spatial_manager.get_ows_endpoint()
        model_db_spatial_manager.gs_api.get_ows_endpoint.assert_called_with(BaseSpatialManager.WORKSPACE, True)

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_get_wms_endpoint(self, _):
        model_db_spatial_manager = _BaseSpatialManager(self.geoserver_engine)
        model_db_spatial_manager.get_wms_endpoint()
        model_db_spatial_manager.gs_api.get_wms_endpoint.assert_called_with(True)

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_reload(self, _):
        spatial_manager = _BaseSpatialManager(self.geoserver_engine)
        ports = ['17500', '8181', '8080']
        spatial_manager.reload(ports=ports, public_endpoint=True)
        spatial_manager.gs_api.reload.assert_called_with(ports, True)
