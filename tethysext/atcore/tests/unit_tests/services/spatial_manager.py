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
from tethysext.atcore.services.exceptions import UnitsNotFound, UnknownUnits
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
    def test_get_projection_units_us_ft(self, _):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=us-ft +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_units(mock_model_db, srid)
        self.assertEqual(SpatialManager.U_IMPERIAL, ret)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_units_ft(self, _):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=ft +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_units(mock_model_db, srid)
        self.assertEqual(SpatialManager.U_IMPERIAL, ret)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_units_m(self, _):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=m +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_units(mock_model_db, srid)
        self.assertEqual(SpatialManager.U_METRIC, ret)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_units_no_units(self, _):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        self.assertRaises(UnitsNotFound, spatial_manager.get_projection_units, mock_model_db, srid)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_units_unknown_units(self, _):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=teva +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        self.assertRaises(UnknownUnits, spatial_manager.get_projection_units, mock_model_db, srid)

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_string(self, _):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_string(mock_model_db, srid)
        spatial_manager.get_projection_string(mock_model_db, srid)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_string_wkt(self, _):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_WKT)
        spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_WKT)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_string_proj4(self, _):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_PROJ4)
        spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_PROJ4)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('proj4text', execute_calls[0][0][0])

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_string_invalid(self, _):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        self.assertRaises(ValueError, spatial_manager.get_projection_string, mock_model_db, srid, 'BAD FORMAT')

    @mock.patch('tethysext.atcore.services.spatial_manager.GeoServerAPI')
    def test_get_projection_string_same_srid_different_format(self, _):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        spatial_manager = SpatialManager(self.geoserver_engine)
        ret = spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_WKT)
        spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_PROJ4)
        spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_PROJ4)
        spatial_manager.get_projection_string(mock_model_db, srid, SpatialManager.PRO_WKT)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(2, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])
        self.assertIn('proj4text', execute_calls[1][0][0])

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
