"""
********************************************************************************
* Name: model_database
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import unittest
import mock
import requests
from tethysext.atcore.services.geoserver_api import GeoServerAPI


class MockGeoServerEngine(object):

    def __init__(self, endpoint, public_endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.public_endpoint = public_endpoint


class MockResponse(object):

    def __init__(self, status_code, text=None, json=None):
        self.status_code = status_code
        self.text = text
        self.json_obj = json

    def json(self):
        return self.json_obj


class GeoServerAPITests(unittest.TestCase):

    def setUp(self):
        self.endpoint = "http://localhost:8181/geoserver/rest/"
        self.username = "admin"
        self.password = "geoserver"
        self.workspace = "foo"
        self.public_endpoint = "http://aquaveo.com/geoserver/rest/"
        self.gwc_endpoint = "http://localhost:8181/geoserver/gwc/rest/"
        self.gwc_public_endpoint = "http://aquaveo.com/geoserver/gwc/rest/"
        self.auth = (self.username, self.password)
        self.gs_engine = MockGeoServerEngine(self.endpoint, self.public_endpoint, self.username, self.password)
        self.gs_api = GeoServerAPI(gs_engine=self.gs_engine)
        self.datastore_name = "hoo"
        self.feature_name = "fee"
        self.tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.test_files_path = os.path.join(self.tests_dir, 'files')

    def tearDown(self):
        pass

    def get_file(self, filename):
        """
        Helper method that renders templates.
        """
        file_path = os.path.join(self.test_files_path, filename)
        with open(file_path, 'r') as f:
            text = f.read()
        return text

    def test_get_ows_endpoint_public(self):
        results = self.gs_api.get_ows_endpoint(self.workspace)
        self.assertEquals("http://aquaveo.com/geoserver/foo/ows/", results)

    def test_get_ows_endpoint_no_public(self):
        results = self.gs_api.get_ows_endpoint(self.workspace, False)
        self.assertEquals('http://localhost:8181/geoserver/foo/ows/', results)

    def test_get_ows_endpoint_trailing_slash(self):
        results = self.gs_api.get_ows_endpoint(self.workspace, False)
        self.assertEquals('http://localhost:8181/geoserver/foo/ows/', results)

    def test_get_ows_endpoint_no_trailing_slash(self):
        self.endpoint = "http://localhost:8181/geoserver/rest"
        self.username = "admin"
        self.password = "geoserver"
        self.workspace = "foo"
        self.public_endpoint = "http://aquaveo.com/geoserver/rest"
        self.gs_engine = MockGeoServerEngine(self.endpoint, self.public_endpoint, self.username, self.password)
        self.gs_api = GeoServerAPI(gs_engine=self.gs_engine)
        results = self.gs_api.get_ows_endpoint(self.workspace, False)
        self.assertEquals('http://localhost:8181/geoserver/foo/ows/', results)

    def test_get_wms_endpoint_public(self):
        results = self.gs_api.get_wms_endpoint()
        self.assertEquals("http://aquaveo.com/geoserver/wms/", results)

    def test_get_wms_endpoint_no_public(self):
        results = self.gs_api.get_wms_endpoint(False)
        self.assertEquals("http://localhost:8181/geoserver/wms/", results)

    def test_get_wms_endpoint_trailing_slash(self):
        results = self.gs_api.get_wms_endpoint()
        self.assertEquals("http://aquaveo.com/geoserver/wms/", results)

    def test_get_wms_endpoint_no_trailing_slash(self):
        self.endpoint = "http://localhost:8181/geoserver/rest"
        self.username = "admin"
        self.password = "geoserver"
        self.workspace = "foo"
        self.public_endpoint = "http://aquaveo.com/geoserver/rest"
        self.gs_engine = MockGeoServerEngine(self.endpoint, self.public_endpoint, self.username, self.password)
        self.gs_api = GeoServerAPI(gs_engine=self.gs_engine)
        results = self.gs_api.get_wms_endpoint()
        self.assertEquals("http://aquaveo.com/geoserver/wms/", results)

    def test_get_gwc_endpoint_public(self):
        results = self.gs_api.get_gwc_endpoint()
        self.assertEquals(self.gwc_public_endpoint, results)

    def test_get_gwc_endpoint_no_public(self):
        results = self.gs_api.get_gwc_endpoint(False)
        self.assertEquals(self.gwc_endpoint, results)

    def test_get_gwc_endpoint_trailing_slash(self):
        results = self.gs_api.get_gwc_endpoint()
        self.assertEquals(self.gwc_public_endpoint, results)

    def test_get_gwc_endpoint_no_trailing_slash(self):
        self.endpoint = "http://localhost:8181/geoserver/rest"
        self.username = "admin"
        self.password = "geoserver"
        self.workspace = "foo"
        self.public_endpoint = "http://aquaveo.com/geoserver/rest"
        self.gs_engine = MockGeoServerEngine(self.endpoint, self.public_endpoint, self.username, self.password)
        self.gs_api = GeoServerAPI(gs_engine=self.gs_engine)
        results = self.gs_api.get_gwc_endpoint()
        self.assertEquals(self.gwc_public_endpoint, results)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_reload_ports_none(self, mock_post):
        mock_post.return_value = MockResponse(200)
        self.gs_api.reload()
        rest_endpoint = self.public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_reload_with_ports(self, mock_post):
        mock_post.return_value = MockResponse(200)
        self.gs_api.reload([17300, 18000])
        rest_endpoint = self.public_endpoint.replace('8181', '17300') + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        rest_endpoint = self.public_endpoint.replace('8181', '18000') + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_reload_not_200(self, mock_post, mock_logger):
        mock_post.return_value = MockResponse(500)
        self.gs_api.reload()
        rest_endpoint = self.public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_reload_connection_error(self, mock_post, mock_logger):
        mock_post.side_effect = requests.ConnectionError()
        self.gs_api.reload()
        rest_endpoint = self.public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_gwc_reload_ports_none(self, mock_post):
        mock_post.return_value = MockResponse(200)
        self.gs_api.gwc_reload()
        rest_endpoint = self.gwc_public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_gwc_reload_with_ports(self, mock_post):
        mock_post.return_value = MockResponse(200)
        self.gs_api.gwc_reload([17300, 18000])
        rest_endpoint = self.gwc_public_endpoint.replace('8181', '17300') + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        rest_endpoint = self.gwc_public_endpoint.replace('8181', '18000') + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_gwc_reload_not_200(self, mock_post, mock_logger):
        mock_post.return_value = MockResponse(500)
        self.gs_api.gwc_reload()
        rest_endpoint = self.gwc_public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_gwc_reload_connection_error(self, mock_post, mock_logger):
        mock_post.side_effect = requests.ConnectionError()
        self.gs_api.gwc_reload()
        rest_endpoint = self.gwc_public_endpoint + 'reload'
        mock_post.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_get_layer_extent(self, mock_get):
        expected_bb = [-14.23, 28.1, -50.42, 89.18]
        jsondict = {
            'featureType': {
                'nativeBoundingBox': {'minx': -12.23, 'miny': 22.1, 'maxx': -56.42, 'maxy': 32.18},
                'latLonBoundingBox': {'minx': -14.23, 'miny': 28.1, 'maxx': -50.42, 'maxy': 89.18}
            }
        }

        mock_get.return_value = MockResponse(200, json=jsondict)
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(  # noqa: E501
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        result = self.gs_api.get_layer_extent(self.workspace, self.datastore_name, self.feature_name, buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        self.assertEquals(expected_bb, result)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_get_layer_extent_native(self, mock_get):
        expected_bb = [-12.23, 22.1, -56.42, 32.18]
        jsondict = {
            'featureType': {
                'nativeBoundingBox': {'minx': -12.23, 'miny': 22.1, 'maxx': -56.42, 'maxy': 32.18},
                'latLonBoundingBox': {'minx': -14.23, 'miny': 28.1, 'maxx': -50.42, 'maxy': 89.18}
            }
        }

        mock_get.return_value = MockResponse(200, json=jsondict)
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(  # noqa: E501
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        result = self.gs_api.get_layer_extent(self.workspace, self.datastore_name, self.feature_name, native=True,
                                              buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        self.assertEquals(expected_bb, result)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_get_layer_extent_feature_bbox_none(self, mock_get):
        expected_bb = [-128.583984375, 22.1874049914, -64.423828125, 52.1065051908]
        jsondict = {}
        mock_get.return_value = MockResponse(200, json=jsondict)
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(  # noqa: E501
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        result = self.gs_api.get_layer_extent(self.workspace, self.datastore_name, self.feature_name, buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        self.assertEquals(expected_bb, result)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_get_layer_extent_not_200(self, mock_get, mock_logger):
        mock_get.return_value = MockResponse(500)
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(  # noqa: E501
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        self.assertRaises(requests.RequestException, self.gs_api.get_layer_extent, self.workspace, self.datastore_name,
                          self.feature_name, buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_postgis_store_validate_connection(self, mock_post):
        mock_post.return_value = MockResponse(201)
        name = 'foo'
        db_host = 'localhost'
        db_port = '5432'
        db_name = 'foo_db'
        db_username = 'user'
        db_password = 'pass'
        max_connections = 10
        max_connection_idle_time = 40
        evictor_run_periodicity = 60

        xml = """
              <dataStore>
                <name>{0}</name>
                <connectionParameters>
                  <entry key="host">{1}</entry>
                  <entry key="port">{2}</entry>
                  <entry key="database">{3}</entry>
                  <entry key="user">{4}</entry>
                  <entry key="passwd">{5}</entry>
                  <entry key="dbtype">postgis</entry>
                  <entry key="max connections">{6}</entry>
                  <entry key="Max connection idle time">{7}</entry>
                  <entry key="Evictor run periodicity">{8}</entry>
                  <entry key="validate connections">{9}</entry>
                </connectionParameters>
              </dataStore>
              """.format(name, db_host, db_port, db_name, db_username, db_password,
                         max_connections, max_connection_idle_time, evictor_run_periodicity,
                         'true')

        expected_headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }

        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores'.format(
            endpoint=self.endpoint,
            workspace=self.workspace
        )
        self.gs_api.create_postgis_store(self.workspace, name, db_host, db_port, db_name, db_username, db_password,
                                         max_connections, max_connection_idle_time, evictor_run_periodicity)
        mock_post.assert_called_with(url=rest_endpoint, data=xml, headers=expected_headers, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_postgis_store_validate_connection_false(self, mock_post):
        mock_post.return_value = MockResponse(201)
        name = 'foo'
        db_host = 'localhost'
        db_port = '5432'
        db_name = 'foo_db'
        db_username = 'user'
        db_password = 'pass'
        max_connections = 10
        max_connection_idle_time = 40
        evictor_run_periodicity = 60

        xml = """
              <dataStore>
                <name>{0}</name>
                <connectionParameters>
                  <entry key="host">{1}</entry>
                  <entry key="port">{2}</entry>
                  <entry key="database">{3}</entry>
                  <entry key="user">{4}</entry>
                  <entry key="passwd">{5}</entry>
                  <entry key="dbtype">postgis</entry>
                  <entry key="max connections">{6}</entry>
                  <entry key="Max connection idle time">{7}</entry>
                  <entry key="Evictor run periodicity">{8}</entry>
                  <entry key="validate connections">{9}</entry>
                </connectionParameters>
              </dataStore>
              """.format(name, db_host, db_port, db_name, db_username, db_password,
                         max_connections, max_connection_idle_time, evictor_run_periodicity,
                         'false')

        expected_headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }

        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores'.format(
            endpoint=self.endpoint,
            workspace=self.workspace
        )
        self.gs_api.create_postgis_store(self.workspace, name, db_host, db_port, db_name, db_username, db_password,
                                         max_connections, max_connection_idle_time, evictor_run_periodicity, False)
        mock_post.assert_called_with(url=rest_endpoint, data=xml, headers=expected_headers, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_postgis_store_not_201(self, mock_post, mock_logger):
        mock_post.return_value = MockResponse(500)
        name = 'foo'
        db_host = 'localhost'
        db_port = '5432'
        db_name = 'foo_db'
        db_username = 'user'
        db_password = 'pass'
        max_connections = 10
        max_connection_idle_time = 40
        evictor_run_periodicity = 60

        xml = """
              <dataStore>
                <name>{0}</name>
                <connectionParameters>
                  <entry key="host">{1}</entry>
                  <entry key="port">{2}</entry>
                  <entry key="database">{3}</entry>
                  <entry key="user">{4}</entry>
                  <entry key="passwd">{5}</entry>
                  <entry key="dbtype">postgis</entry>
                  <entry key="max connections">{6}</entry>
                  <entry key="Max connection idle time">{7}</entry>
                  <entry key="Evictor run periodicity">{8}</entry>
                  <entry key="validate connections">{9}</entry>
                </connectionParameters>
              </dataStore>
              """.format(name, db_host, db_port, db_name, db_username, db_password,
                         max_connections, max_connection_idle_time, evictor_run_periodicity,
                         'true')

        expected_headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }

        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores'.format(
            endpoint=self.endpoint,
            workspace=self.workspace
        )

        self.assertRaises(requests.RequestException, self.gs_api.create_postgis_store, self.workspace, name, db_host,
                          db_port, db_name, db_username, db_password, max_connections, max_connection_idle_time,
                          evictor_run_periodicity)
        mock_logger.error.assert_called()
        mock_post.assert_called_with(url=rest_endpoint, data=xml, headers=expected_headers, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer(self, mock_post, mock_put, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=201)
        mock_put.return_value = mock.MagicMock(status_code=200)
        datastore_name = 'foo'
        feature_name = 'bar'
        geometry_type = 'Point'
        srid = 4236
        sql = 'SELECT * FROM foo'
        default_style = 'points'

        self.gs_api.create_layer(self.workspace, datastore_name, feature_name, geometry_type, srid, sql, default_style)

        # Validate endpoint calls
        sql_view_url = 'workspaces/{workspace}/datastores/{datastore}/featuretypes'.format(
            workspace=self.workspace,
            datastore=datastore_name
        )
        layer_url = 'layers/{feature_name}.xml'.format(
            feature_name=feature_name
        )
        gwc_layer_url = 'layers/{workspace}:{feature_name}.xml'.format(
            workspace=self.workspace,
            feature_name=feature_name
        )

        expected_sql_xml = self.get_file('test_create_layer_sql_view.xml')
        expected_layer_xml = self.get_file('test_create_layer_layer.xml')
        expected_gwc_lyr_xml = self.get_file('test_create_layer_gwc_layer.xml')

        # Create feature type call
        post_call_args = mock_post.call_args_list
        self.assertIn(sql_view_url, post_call_args[0][0][0])
        self.assertEqual(expected_sql_xml, post_call_args[0][1]['data'])

        # Create layer call
        put_call_args = mock_put.call_args_list
        self.assertIn(layer_url, put_call_args[0][0][0])
        self.assertEqual(expected_layer_xml, str(put_call_args[0][1]['data']))

        # GWC Call
        self.assertIn(gwc_layer_url, put_call_args[1][0][0])
        self.assertEqual(expected_gwc_lyr_xml, str(put_call_args[1][1]['data']))
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_create_feature_type_already_exists(self, mock_post, mock_put, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500, text='already exists')
        mock_put.return_value = mock.MagicMock(status_code=200)
        datastore_name = 'foo'
        feature_name = 'bar'
        geometry_type = 'Point'
        srid = 4236
        sql = 'SELECT * FROM foo'
        default_style = 'points'

        self.gs_api.create_layer(self.workspace, datastore_name, feature_name, geometry_type, srid, sql,
                                 default_style)

        # Validate endpoint calls
        sql_view_url = 'workspaces/{workspace}/datastores/{datastore}/featuretypes'.format(
            workspace=self.workspace,
            datastore=datastore_name
        )
        layer_url = 'layers/{feature_name}.xml'.format(
            feature_name=feature_name
        )
        gwc_layer_url = 'layers/{workspace}:{feature_name}.xml'.format(
            workspace=self.workspace,
            feature_name=feature_name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(sql_view_url, post_call_args[0][0][0])

        # Create layer call
        put_call_args = mock_put.call_args_list
        self.assertIn(layer_url, put_call_args[0][0][0])

        # GWC Call
        self.assertIn(gwc_layer_url, put_call_args[1][0][0])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_create_feature_type_error(self, mock_post, mock_put, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500, text='server error')
        mock_put.return_value = mock.MagicMock(status_code=200)
        datastore_name = 'foo'
        feature_name = 'bar'
        geometry_type = 'Point'
        srid = 4236
        sql = 'SELECT * FROM foo'
        default_style = 'points'

        self.assertRaises(requests.RequestException, self.gs_api.create_layer, self.workspace, datastore_name,
                          feature_name, geometry_type, srid, sql, default_style)

        # Validate endpoint calls
        sql_view_url = 'workspaces/{workspace}/datastores/{datastore}/featuretypes'.format(
            workspace=self.workspace,
            datastore=datastore_name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(sql_view_url, post_call_args[0][0][0])

        mock_put.assert_not_called()
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_create_layer_error(self, mock_post, mock_put, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=201)
        mock_put.return_value = mock.MagicMock(status_code=500)
        datastore_name = 'foo'
        feature_name = 'bar'
        geometry_type = 'Point'
        srid = 4236
        sql = 'SELECT * FROM foo'
        default_style = 'points'

        self.assertRaises(requests.RequestException, self.gs_api.create_layer, self.workspace, datastore_name,
                          feature_name, geometry_type, srid, sql, default_style)

        # Validate endpoint calls
        sql_view_url = 'workspaces/{workspace}/datastores/{datastore}/featuretypes'.format(
            workspace=self.workspace,
            datastore=datastore_name
        )
        layer_url = 'layers/{feature_name}.xml'.format(
            feature_name=feature_name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(sql_view_url, post_call_args[0][0][0])

        # Create layer call
        put_call_args = mock_put.call_args_list
        self.assertIn(layer_url, put_call_args[0][0][0])
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_create_gwc_layer_error(self, mock_post, mock_put, mock_logger):

        def handle_put(url, **kwargs):
            if 'gwc/rest' in url:
                return mock.MagicMock(status_code=500)
            else:
                return mock.MagicMock(status_code=200)

        mock_post.return_value = mock.MagicMock(status_code=201)
        mock_put.side_effect = handle_put
        datastore_name = 'foo'
        feature_name = 'bar'
        geometry_type = 'Point'
        srid = 4236
        sql = 'SELECT * FROM foo'
        default_style = 'points'

        self.assertRaises(requests.RequestException, self.gs_api.create_layer, self.workspace, datastore_name,
                          feature_name, geometry_type, srid, sql, default_style)

        # Validate endpoint calls
        sql_view_url = 'workspaces/{workspace}/datastores/{datastore}/featuretypes'.format(
            workspace=self.workspace,
            datastore=datastore_name
        )
        layer_url = 'layers/{feature_name}.xml'.format(
            feature_name=feature_name
        )
        gwc_layer_url = 'layers/{workspace}:{feature_name}.xml'.format(
            workspace=self.workspace,
            feature_name=feature_name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(sql_view_url, post_call_args[0][0][0])

        # Create layer call
        put_call_args = mock_put.call_args_list
        self.assertIn(layer_url, put_call_args[0][0][0])

        # GWC Call
        self.assertIn(gwc_layer_url, put_call_args[1][0][0])
        mock_logger.error.assert_called()
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_group(self, mock_post):
        mock_post.return_value = mock.MagicMock(status_code=201)
        group_name = 'test_group'
        layer_names = ['layer1', 'layer2']
        default_styles = ['style1', 'style2']
        self.gs_api.create_layer_group(self.workspace, group_name, layer_names, default_styles)

        # Validate endpoint calls
        layer_group_url = 'workspaces/{w}/layergroups.json'.format(
            w=self.workspace
        )
        expected_xml = self.get_file('test_create_layer_group.xml')

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(layer_group_url, post_call_args[0][0][0])
        self.assertEqual(expected_xml, str(post_call_args[0][1]['data']))

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_layer_group_error(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500)
        group_name = 'test_group'
        layer_names = ['layer1', 'layer2']
        default_styles = ['style1', 'style2']
        self.assertRaises(requests.RequestException, self.gs_api.create_layer_group, self.workspace, group_name,
                          layer_names, default_styles)

        # Validate endpoint calls
        layer_group_url = 'workspaces/{w}/layergroups.json'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(layer_group_url, post_call_args[0][0][0])
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=201)
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.gs_api.create_style(self.workspace, style_name, sld_template, sld_context)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style_cannot_find_style(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500, text='Unable to find style for event')
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.gs_api.create_style(self.workspace, style_name, sld_template, sld_context)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style_error_persisting(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500, text='Error persisting')
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.gs_api.create_style(self.workspace, style_name, sld_template, sld_context)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style_other_500(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500, text='foo bar')
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.assertRaises(requests.RequestException, self.gs_api.create_style, self.workspace, style_name,
                          sld_template, sld_context)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style_other_error(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=403)
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.assertRaises(requests.RequestException, self.gs_api.create_style, self.workspace, style_name,
                          sld_template, sld_context)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_style_overwrite_no_such_style(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=201)
        self.delete_style = mock.MagicMock()
        self.delete_style.side_effect = Exception('no such style')
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.gs_api.create_style(self.workspace, style_name, sld_template, sld_context, overwrite=True)

        # Validate endpoint calls
        style_url = 'workspaces/{w}/styles'.format(
            w=self.workspace
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(style_url, post_call_args[0][0][0])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    def test_create_style_overwrite_referenced_by_existing(self, mock_logger):
        self.gs_api.delete_style = mock.MagicMock()
        self.gs_api.delete_style.side_effect = ValueError('referenced by existing')
        style_name = 'style_name'
        sld_template = os.path.join(self.test_files_path, 'test_create_style.sld')
        sld_context = {'foo': 'bar'}
        self.assertRaises(ValueError, self.gs_api.create_style, self.workspace, style_name,
                          sld_template, sld_context, overwrite=True)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer(self, mock_delete):
        mock_delete.return_value = mock.MagicMock(status_code=200)
        datastore = 'datastore_name'
        name = 'layer_name'

        self.gs_api.delete_layer(self.workspace, datastore, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/datastores/{d}/featuretypes/{f}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            d=datastore,
            f=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'recurse': False}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer_warning(self, mock_delete, mock_logger):
        mock_delete.return_value = mock.MagicMock(status_code=404)
        datastore = 'datastore_name'
        name = 'layer_name'

        self.gs_api.delete_layer(self.workspace, datastore, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/datastores/{d}/featuretypes/{f}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            d=datastore,
            f=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'recurse': False}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer_exception(self, mock_delete, mock_logger):
        mock_delete.return_value = mock.MagicMock(status_code=500)
        datastore = 'datastore_name'
        name = 'layer_name'

        self.assertRaises(requests.RequestException, self.gs_api.delete_layer, self.workspace, datastore, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/datastores/{d}/featuretypes/{f}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            d=datastore,
            f=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'recurse': False}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer_group(self, mock_delete):
        mock_delete.return_value = mock.MagicMock(status_code=200)
        name = 'layer_group_name'

        self.gs_api.delete_layer_group(self.workspace, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/layergroups/{lg}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            lg=name
        )

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer_group_no_group(self, mock_delete):
        mock_delete.return_value = mock.MagicMock(status_code=404, text='No such layer group')
        name = 'layer_group_name'

        self.gs_api.delete_layer_group(self.workspace, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/layergroups/{lg}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            lg=name
        )

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_layer_group_exception(self, mock_delete, mock_logger):
        mock_delete.return_value = mock.MagicMock(status_code=404, text="These aren't the droids you're looking for...")
        name = 'layer_group_name'

        self.assertRaises(requests.RequestException, self.gs_api.delete_layer_group, self.workspace, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/layergroups/{lg}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            lg=name
        )

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth)
        mock_logger.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_style(self, mock_delete):
        mock_delete.return_value = mock.MagicMock(status_code=200)
        name = 'style_name'

        self.gs_api.delete_style(self.workspace, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/styles/{s}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            s=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'purge': False}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_style_warning(self, mock_delete, mock_logger):
        mock_delete.return_value = mock.MagicMock(status_code=404)
        name = 'style_name'

        self.gs_api.delete_style(self.workspace, name, purge=True)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/styles/{s}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            s=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'purge': True}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)
        mock_logger.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_style_exception(self, mock_delete, mock_logger):
        mock_delete.return_value = mock.MagicMock(status_code=500)
        name = 'style_name'

        self.assertRaises(requests.RequestException, self.gs_api.delete_style, self.workspace, name)

        # Validate endpoint calls
        url = '{endpoint}workspaces/{w}/styles/{s}'.format(
            endpoint=self.endpoint,
            w=self.workspace,
            s=name
        )

        headers = {
            "Content-type": "application/json"
        }

        params = {'purge': False}

        # Create feature type call
        mock_delete.assert_called_with(url, auth=self.auth, headers=headers, params=params)
        mock_logger.error.assert_called()

    def test_modify_tile_cache_invalid_operation(self):
        name = 'gwc_layer_name'
        operation = 'invalid-operation'
        self.assertRaises(ValueError, self.gs_api.modify_tile_cache, self.workspace, name, operation)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_modify_tile_cache_mass_truncate(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=200)
        name = 'gwc_layer_name'
        operation = self.gs_api.GWC_OP_MASS_TRUNCATE
        self.gs_api.modify_tile_cache(self.workspace, name, operation)

        url = 'masstruncate/'.format(endpoint=self.gs_api.get_gwc_endpoint())

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(url, post_call_args[0][0][0])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_modify_tile_cache_seed(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=200)
        name = 'gwc_layer_name'
        operation = self.gs_api.GWC_OP_SEED
        self.gs_api.modify_tile_cache(self.workspace, name, operation)

        url = 'seed/{workspace}:{name}.xml'.format(
            workspace=self.workspace,
            name=name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(url, post_call_args[0][0][0])
        self.assertIn(operation, post_call_args[0][1]['data'])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_modify_tile_cache_reseed(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=200)
        name = 'gwc_layer_name'
        operation = self.gs_api.GWC_OP_RESEED
        self.gs_api.modify_tile_cache(self.workspace, name, operation)

        url = 'seed/{workspace}:{name}.xml'.format(
            workspace=self.workspace,
            name=name
        )

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(url, post_call_args[0][0][0])
        self.assertIn(operation, post_call_args[0][1]['data'])
        mock_logger.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_modify_tile_cache_exception(self, mock_post, mock_logger):
        mock_post.return_value = mock.MagicMock(status_code=500)
        name = 'gwc_layer_name'
        operation = self.gs_api.GWC_OP_MASS_TRUNCATE
        self.assertRaises(requests.RequestException, self.gs_api.modify_tile_cache, self.workspace, name, operation)

        url = 'masstruncate/'.format(endpoint=self.gs_api.get_gwc_endpoint())

        # Create feature type call
        post_call_args = mock_post.call_args_list
        # call_args[call_num][0=args|1=kwargs][arg_index|kwarg_key]
        self.assertIn(url, post_call_args[0][0][0])
        mock_logger.error.assert_called()

    def test_terminate_tile_cache_tasks_invalid_operation(self):
        name = 'gwc_layer_name'
        operation = 'invalid-operation'
        self.assertRaises(ValueError, self.gs_api.terminate_tile_cache_tasks, self.workspace, name, kill=operation)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_terminate_tile_cache_tasks(self, mock_post):
        mock_post.return_value = mock.MagicMock(status_code=200)
        name = 'gwc_layer_name'

        self.gs_api.terminate_tile_cache_tasks(self.workspace, name)

        url = '{endpoint}seed/{workspace}:{name}'.format(
            endpoint=self.gs_api.get_gwc_endpoint(),
            workspace=self.workspace,
            name=name
        )

        # Create feature type call
        mock_post.assert_called_with(url, auth=self.auth, data={'kill_all': self.gs_api.GWC_KILL_ALL})

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_terminate_tile_cache_tasks_exception(self, mock_post):
        mock_post.return_value = mock.MagicMock(status_code=500)
        name = 'gwc_layer_name'

        self.assertRaises(requests.RequestException, self.gs_api.terminate_tile_cache_tasks, self.workspace, name)

        url = '{endpoint}seed/{workspace}:{name}'.format(
            endpoint=self.gs_api.get_gwc_endpoint(),
            workspace=self.workspace,
            name=name
        )

        # Create feature type call
        mock_post.assert_called_with(url, auth=self.auth, data={'kill_all': self.gs_api.GWC_KILL_ALL})

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_query_tile_cache_tasks(self, mock_get):
        mock_response = mock.MagicMock(status_code=200)
        mock_response.json.return_value = {'long-array-array': [
            [1, 100, 99, 1, 1],
            [10, 100, 90, 2, -2]
        ]}
        mock_get.return_value = mock_response
        name = 'gwc_layer_name'
        ret = self.gs_api.query_tile_cache_tasks(self.workspace, name)

        url = '{endpoint}seed/{workspace}:{name}.json'.format(
            endpoint=self.gs_api.get_gwc_endpoint(),
            workspace=self.workspace,
            name=name
        )

        # Create feature type call
        mock_get.assert_called_with(url, auth=self.auth)

        self.assertIsInstance(ret, list)
        self.assertEqual(2, len(ret))
        self.assertEqual({'tiles_processed': 1, 'total_to_process': 100, 'num_remaining': 99,
                          'task_id': 1, 'task_status': 'Running'}, ret[0])
        self.assertEqual({'tiles_processed': 10, 'total_to_process': 100, 'num_remaining': 90,
                          'task_id': 2, 'task_status': -2}, ret[1])

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_query_tile_cache_tasks_exception(self, mock_get):
        mock_response = mock.MagicMock(status_code=500)
        mock_get.return_value = mock_response
        name = 'gwc_layer_name'
        self.assertRaises(requests.RequestException, self.gs_api.query_tile_cache_tasks, self.workspace, name)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_coverage_store(self, mock_post):
        mock_response = mock.MagicMock(status_code=201)
        mock_post.return_value = mock_response
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        self.gs_api.create_coverage_store(self.workspace, coverage_name, coverage_type)
        mock_post.assert_called()
        post_call_args = mock_post.call_args_list
        url = 'workspaces/{workspace}/coveragestores'.format(
            workspace=self.workspace
        )
        self.assertIn(url, post_call_args[0][1]['url'])
        self.assertIn(coverage_name, post_call_args[0][1]['data'])
        self.assertIn(coverage_type, post_call_args[0][1]['data'])

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_coverage_store_grass_grid(self, mock_post):
        mock_response = mock.MagicMock(status_code=201)
        mock_post.return_value = mock_response
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        self.gs_api.create_coverage_store(self.workspace, coverage_name, coverage_type)
        mock_post.assert_called()
        post_call_args = mock_post.call_args_list
        url = 'workspaces/{workspace}/coveragestores'.format(
            workspace=self.workspace
        )
        self.assertIn(url, post_call_args[0][1]['url'])
        self.assertIn(coverage_name, post_call_args[0][1]['data'])
        self.assertIn(GeoServerAPI.CT_ARC_GRID, post_call_args[0][1]['data'])
        self.assertNotIn(GeoServerAPI.CT_GRASS_GRID, post_call_args[0][1]['data'])

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.post')
    def test_create_coverage_store_exception(self, mock_post):
        mock_response = mock.MagicMock(status_code=500)
        mock_post.return_value = mock_response
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        self.assertRaises(requests.RequestException, self.gs_api.create_coverage_store, self.workspace,
                          coverage_name, coverage_type)

    def test_create_coverage_store_invalid_type(self):
        coverage_name = 'foo'
        coverage_type = 'INVALID_COVERAGE_TYPE'
        self.assertRaises(ValueError, self.gs_api.create_coverage_store, self.workspace,
                          coverage_name, coverage_type)

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=201)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        coverage_file = os.path.join(self.test_files_path, 'arc_grid', 'precip30min.asc')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=coverage_type.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_already_exists(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=500, text='already exists')
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        coverage_file = os.path.join(self.test_files_path, 'arc_grid', 'precip30min.asc')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=coverage_type.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_error_unzipping(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=500, text='Error occured unzipping file')
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        coverage_file = os.path.join(self.test_files_path, 'arc_grid', 'precip30min.asc')
        self.assertRaises(requests.RequestException, self.gs_api.create_coverage_layer, workspace=self.workspace,
                          coverage_name=coverage_name, coverage_type=coverage_type, coverage_file=coverage_file)
        num_put_calls = len(mock_put.call_args_list)
        self.assertEqual(5, num_put_calls)
        mock_log.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_error(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=500)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        coverage_file = os.path.join(self.test_files_path, 'arc_grid', 'precip30min.asc')
        self.assertRaises(requests.RequestException, self.gs_api.create_coverage_layer, workspace=self.workspace,
                          coverage_name=coverage_name, coverage_type=coverage_type, coverage_file=coverage_file)
        num_put_calls = len(mock_put.call_args_list)
        self.assertEqual(3, num_put_calls)
        mock_log.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_zip(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=201)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_ARC_GRID
        coverage_file = os.path.join(self.test_files_path, 'arc_grid', 'precip30min.zip')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=coverage_type.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_grass_grid(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=201)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo.ele')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=GeoServerAPI.CT_ARC_GRID.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_grass_grid_zip(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=201)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo.zip')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=GeoServerAPI.CT_ARC_GRID.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.put')
    def test_create_coverage_layer_grass_grid_zip_with_dir(self, mock_put, mock_log):
        mock_response = mock.MagicMock(status_code=201)
        mock_put.return_value = mock_response
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo_with_dir.zip')
        self.gs_api.create_coverage_layer(workspace=self.workspace, coverage_name=coverage_name,
                                          coverage_type=coverage_type, coverage_file=coverage_file)
        mock_put.assert_called()
        put_call_args = mock_put.call_args_list
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}/file.{extension}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
            extension=GeoServerAPI.CT_ARC_GRID.lower()
        )
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertIn('coverageName', put_call_args[0][1]['params'])
        self.assertEqual(coverage_name, put_call_args[0][1]['params']['coverageName'])
        self.assertIn('files', put_call_args[0][1])
        self.gs_api.update_layer_styles.assert_called()
        mock_log.info.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    def test_create_coverage_layer_grass_grid_corrupt_file(self, mock_log):
        self.gs_api.update_layer_styles = mock.MagicMock()
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo_corrupt.ele')
        self.assertRaises(IOError, self.gs_api.create_coverage_layer, workspace=self.workspace,
                          coverage_name=coverage_name, coverage_type=coverage_type, coverage_file=coverage_file)
        mock_log.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    def test_create_coverage_layer_grass_grid_invalid_zip(self, mock_log):
        coverage_name = 'foo'
        coverage_type = GeoServerAPI.CT_GRASS_GRID
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo_invalid.zip')
        self.assertRaises(ValueError, self.gs_api.create_coverage_layer, workspace=self.workspace,
                          coverage_name=coverage_name, coverage_type=coverage_type, coverage_file=coverage_file)
        mock_log.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    def test_create_coverage_layer_invalid_coverage_type(self, mock_log):
        coverage_name = 'foo'
        coverage_type = 'INVALID_COVERAGE_TYPE'
        coverage_file = os.path.join(self.test_files_path, 'grass_grid', 'provo_invalid.zip')
        self.assertRaises(ValueError, self.gs_api.create_coverage_layer, workspace=self.workspace,
                          coverage_name=coverage_name, coverage_type=coverage_type, coverage_file=coverage_file)
        mock_log.error.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_coverage_store(self, mock_delete):
        mock_response = mock.MagicMock(status_code=200)
        mock_delete.return_value = mock_response

        coverage_name = 'foo'
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
        )

        json = {'recurse': True,
                'purge': True}

        self.gs_api.delete_coverage_store(workspace=self.workspace, name=coverage_name)
        put_call_args = mock_delete.call_args_list
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertEqual(json, put_call_args[0][1]['params'])
        self.assertEqual({"Content-type": "application/json"}, put_call_args[0][1]['headers'])

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_coverage_store_with_warning(self, mock_delete, mock_log):
        mock_response = mock.MagicMock(status_code=403)
        mock_delete.return_value = mock_response

        coverage_name = 'foo'
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
        )

        json = {'recurse': True,
                'purge': True}

        self.gs_api.delete_coverage_store(workspace=self.workspace, name=coverage_name)

        put_call_args = mock_delete.call_args_list
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertEqual(json, put_call_args[0][1]['params'])
        self.assertEqual({"Content-type": "application/json"}, put_call_args[0][1]['headers'])
        mock_log.warning.assert_called()

    @mock.patch('tethysext.atcore.services.geoserver_api.log')
    @mock.patch('tethysext.atcore.services.geoserver_api.requests.delete')
    def test_delete_coverage_store_with_error(self, mock_delete, mock_log):
        mock_response = mock.MagicMock(status_code=500)
        mock_delete.return_value = mock_response

        coverage_name = 'foo'
        url = 'workspaces/{workspace}/coveragestores/{coverage_store_name}'.format(
            workspace=self.workspace,
            coverage_store_name=coverage_name,
        )

        json = {'recurse': True,
                'purge': True}

        self.assertRaises(requests.RequestException, self.gs_api.delete_coverage_store, workspace=self.workspace,
                          name=coverage_name)

        put_call_args = mock_delete.call_args_list
        self.assertIn(url, put_call_args[0][1]['url'])
        self.assertEqual(json, put_call_args[0][1]['params'])
        self.assertEqual({"Content-type": "application/json"}, put_call_args[0][1]['headers'])

        mock_log.error.assert_called()
