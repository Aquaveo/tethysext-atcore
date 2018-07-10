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
from tethysext.atcore.services.spatial_manager import SpatialManager, reload_config


class Foo(SpatialManager):
    """For testing the reload_config decorator."""
    @reload_config()
    def test_decorator(self, reload_config=True):
        return reload_config


class SpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()

    def tearDown(self):
        pass

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_reload_config_decorator(self, _):
        foo = Foo(self.geoserver_engine)
        ret = foo.test_decorator()
        self.assertTrue(ret)
        foo.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_reload_config_decorator_no_reload_config(self, _):
        foo = Foo(self.geoserver_engine)
        ret = foo.test_decorator(reload_config=False)
        self.assertFalse(ret)
        foo.gs_api.reload.assert_not_called()

    def test_reload_config_decorator_non_method(self):
        @reload_config()
        def not_a_method(number, string):
            pass

        self.assertRaises(ValueError, not_a_method, 1, 'foo')

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_ows_endpoint(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        spatial_manager.get_ows_endpoint()
        spatial_manager.gs_api.get_ows_endpoint.assert_called_with(SpatialManager.WORKSPACE, True)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_wms_endpoint(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        spatial_manager.get_wms_endpoint()
        spatial_manager.gs_api.get_wms_endpoint.assert_called_with(True)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_link_geoserver_to_db(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        mock_url = mock.MagicMock(host='localhost', port='5432', database='db1', username='foo', password='pass')
        mock_modeldatabase = mock.MagicMock(db_url_obj=mock_url)
        mock_modeldatabase.get_id.return_value = 'I001'
        spatial_manager.link_geoserver_to_db(mock_modeldatabase, True)
        spatial_manager.gs_api.create_postgis_store.assert_called_with(workspace=SpatialManager.WORKSPACE,
                                                                       name='I001',
                                                                       db_host='localhost',
                                                                       db_port='5432',
                                                                       db_name='db1',
                                                                       db_username='foo',
                                                                       db_password='pass')
        spatial_manager.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_link_geoserver_to_db_with_out_reload_config(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        mock_url = mock.MagicMock(host='localhost', port='5432', database='db1', username='foo', password='pass')
        mock_modeldatabase = mock.MagicMock(db_url_obj=mock_url)
        mock_modeldatabase.get_id.return_value = 'I001'
        spatial_manager.link_geoserver_to_db(mock_modeldatabase, False)
        spatial_manager.gs_api.create_postgis_store.assert_called_with(workspace=SpatialManager.WORKSPACE,
                                                                       name='I001',
                                                                       db_host='localhost',
                                                                       db_port='5432',
                                                                       db_name='db1',
                                                                       db_username='foo',
                                                                       db_password='pass')
        spatial_manager.gs_api.reload.assert_not_called()

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_unlink_geoserver_from_db(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        spatial_manager.get_db_specific_store_id = mock.MagicMock(return_value='Workspace:S001')
        spatial_manager.unlink_geoserver_from_db(model_db=mock.MagicMock())
        self.geoserver_engine.delete_store.assert_called_with('Workspace:S001', purge=False, recurse=False)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_create_workspace(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        spatial_manager.create_workspace()
        self.geoserver_engine.create_workspace.assert_called_with(SpatialManager.WORKSPACE, SpatialManager.URI)
        spatial_manager.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_db_specific_store_id(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        mock_modeldatabase = mock.MagicMock()
        mock_modeldatabase.get_id.return_value = 'I001'
        expected_Result = spatial_manager.get_db_specific_store_id(mock_modeldatabase)
        self.assertEqual('{}:{}'.format(SpatialManager.WORKSPACE, 'I001'), expected_Result)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_reload(self, _):
        spatial_manager = SpatialManager(self.geoserver_engine)
        ports = ['17500', '8181', '8080']
        spatial_manager.reload(ports=ports, public_endpoint=True)
        spatial_manager.gs_api.reload.assert_called_with(ports, True)
