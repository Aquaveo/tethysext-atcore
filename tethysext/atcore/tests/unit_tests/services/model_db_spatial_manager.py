"""
********************************************************************************
* Name: model_db_spatial_manager.py
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
import unittest
from tethysext.atcore.services.exceptions import UnitsNotFound, UnknownUnits
from tethysext.atcore.services.model_db_spatial_manager import ModelDBSpatialManager
from tethysext.atcore.services.base_spatial_manager import reload_config


class _ModelDBSpatialManager(ModelDBSpatialManager):

    @reload_config()
    def test_decorator(self, reload_config=True):
        return reload_config

    def get_extent_for_project(self, model_db):
        return [-1, 1, -1, 1]


class ModelDBSpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()

    def tearDown(self):
        pass

    def test_get_projection_units_ft(self):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=ft +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_units(mock_model_db, srid)
        self.assertEqual(ModelDBSpatialManager.U_IMPERIAL, ret)

    def test_get_projection_units_m(self):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=m +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_units(mock_model_db, srid)
        self.assertEqual(ModelDBSpatialManager.U_METRIC, ret)

    def test_get_projection_units_no_units(self):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        self.assertRaises(UnitsNotFound, model_db_spatial_manager.get_projection_units, mock_model_db, srid)

    def test_get_projection_units_unknown_units(self):
        srid = 2232
        mock_row = mock.MagicMock(proj4text='+proj=utm +zone=20 +datum=WGS84 +units=teva +no_defs ')
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        self.assertRaises(UnknownUnits, model_db_spatial_manager.get_projection_units, mock_model_db, srid)

    def test_get_projection_string(self):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_string(mock_model_db, srid)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])

    def test_get_projection_string_wkt(self):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_WKT)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_WKT)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])

    def test_get_projection_string_proj4(self):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_PROJ4)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_PROJ4)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(1, len(execute_calls))
        self.assertIn('proj4text', execute_calls[0][0][0])

    def test_get_projection_string_invalid(self):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        self.assertRaises(ValueError, model_db_spatial_manager.get_projection_string, mock_model_db, srid, 'BAD FORMAT')

    def test_get_projection_string_same_srid_different_format(self):
        srid = 2232
        mock_project_string = 'FAKE PROJECTION STRING'
        mock_row = mock.MagicMock(proj_string=mock_project_string)
        mock_engine = mock.MagicMock()
        mock_engine.execute.return_value = [mock_row]
        mock_model_db = mock.MagicMock()
        mock_model_db.get_engine.return_value = mock_engine
        model_db_spatial_manager = ModelDBSpatialManager(self.geoserver_engine)
        ret = model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_WKT)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_PROJ4)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_PROJ4)
        model_db_spatial_manager.get_projection_string(mock_model_db, srid, ModelDBSpatialManager.PRO_WKT)
        execute_calls = mock_engine.execute.call_args_list
        self.assertEqual(mock_project_string, ret)
        self.assertEqual(2, len(execute_calls))
        self.assertIn('srtext', execute_calls[0][0][0])
        self.assertIn('proj4text', execute_calls[1][0][0])

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_link_geoserver_to_db(self, _):
        model_db_spatial_manager = _ModelDBSpatialManager(self.geoserver_engine)
        mock_url = mock.MagicMock(host='localhost', port='5432', database='db1', username='foo', password='pass')
        mock_modeldatabase = mock.MagicMock(db_url_obj=mock_url)
        mock_modeldatabase.get_id.return_value = 'I001'
        model_db_spatial_manager.link_geoserver_to_db(mock_modeldatabase, True)
        model_db_spatial_manager.gs_api.create_postgis_store.\
            assert_called_with(workspace=ModelDBSpatialManager.WORKSPACE,
                               name='I001',
                               db_host='localhost',
                               db_port='5432',
                               db_name='db1',
                               db_username='foo',
                               db_password='pass')
        model_db_spatial_manager.gs_api.reload.assert_called()

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_link_geoserver_to_db_with_out_reload_config(self, _):
        model_db_spatial_manager = _ModelDBSpatialManager(self.geoserver_engine)
        mock_url = mock.MagicMock(host='localhost', port='5432', database='db1', username='foo', password='pass')
        mock_modeldatabase = mock.MagicMock(db_url_obj=mock_url)
        mock_modeldatabase.get_id.return_value = 'I001'
        model_db_spatial_manager.link_geoserver_to_db(mock_modeldatabase, False)
        model_db_spatial_manager.gs_api.create_postgis_store.\
            assert_called_with(workspace=ModelDBSpatialManager.WORKSPACE,
                               name='I001',
                               db_host='localhost',
                               db_port='5432',
                               db_name='db1',
                               db_username='foo',
                               db_password='pass')
        model_db_spatial_manager.gs_api.reload.assert_not_called()

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_unlink_geoserver_from_db(self, _):
        model_db_spatial_manager = _ModelDBSpatialManager(self.geoserver_engine)
        model_db_spatial_manager.get_db_specific_store_id = mock.MagicMock(return_value='Workspace:S001')
        model_db_spatial_manager.unlink_geoserver_from_db(model_db=mock.MagicMock())
        self.geoserver_engine.delete_store.assert_called_with('Workspace:S001', purge=False, recurse=False)
