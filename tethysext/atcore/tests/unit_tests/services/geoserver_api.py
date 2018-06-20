"""
********************************************************************************
* Name: model_database
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
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

    def tearDown(self):
        pass

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
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(
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
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        result = self.gs_api.get_layer_extent(self.workspace, self.datastore_name, self.feature_name, native=True, buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        self.assertEquals(expected_bb, result)

    @mock.patch('tethysext.atcore.services.geoserver_api.requests.get')
    def test_get_layer_extent_feature_bbox_none(self, mock_get):
        expected_bb = [-128.583984375, 22.1874049914, -64.423828125, 52.1065051908]
        jsondict = {}
        mock_get.return_value = MockResponse(200, json=jsondict)
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(
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
        rest_endpoint = '{endpoint}workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_name}.json'.format(
            endpoint=self.endpoint,
            workspace=self.workspace,
            datastore=self.datastore_name,
            feature_name=self.feature_name
        )
        self.assertRaises(requests.RequestException, self.gs_api.get_layer_extent, self.workspace, self.datastore_name, self.feature_name, buffer_factor=1.0)
        mock_get.assert_called_with(rest_endpoint, auth=self.auth)
        mock_logger.error.assert_called()

    def test_create_postgis_store_validate_connection(self):
        pass

    def test_create_postgis_store_validate_connection_false(self):
        pass

    def test_create_postgis_store_validate_connection_error_response(self):
        pass

    def test_create_layer_create_new(self):
        pass

    def test_create_layer_create_existing(self):
        pass

    def test_create_layer_create_error(self):
        pass

    def test_create_layer_group(self):
        pass

    def test_create_style_new_style(self):
        pass

    def test_create_style_cannot_find_style(self):
        pass

    def test_delete_layer(self):
        pass

    def test_delete_layer_exception(self):
        pass

    def test_delete_layer_group(self):
        pass

    def test_delete_layer_group_no_group(self):
        pass

    def test_delete_style(self):
        pass

    def test_delete_style_exception(self):
        pass

    def test_modify_tile_cache_GWC_OPERATIONS(self):
        pass

    def test_modify_tile_cache_GWC_OP_MASS_TRUNCATE(self):
        pass

    def test_modify_tile_cache(self):
        pass

    def test_modify_tile_cache_exception(self):
        pass

    def test_terminate_tile_cache_tasks_not_GWC_KILL_OPERATIONS(self):
        pass

    def test_terminate_tile_cache_tasks_GWC_KILL_OPERATIONS(self):
        pass

    def test_terminate_tile_cache_tasks_exception(self):
        pass

    def test_query_tile_cache_tasks(self):
        pass

    def test_query_tile_cache_tasks_exception(self):
        pass













































