from unittest import mock
import unittest
from tethysext.atcore.services.resource_spatial_manager import ResourceSpatialManager


class ResourceSpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()
        self.datastore_name = 'test_store'
        self.resource_id = 'test_resource_id'

    def tearDown(self):
        pass

    def test_get_projection_units(self):
        geoserver_engine = mock.MagicMock()
        spatial_manager = ResourceSpatialManager(geoserver_engine)
        projection = spatial_manager.get_projection_units()
        self.assertEqual(projection, '<units>')

    def test_get_projection_string(self):
        geoserver_engine = mock.MagicMock()
        spatial_manager = ResourceSpatialManager(geoserver_engine)
        projection = spatial_manager.get_projection_string()
        self.assertEqual(projection, "<projection string>")

    def test_get_extent_for_project(self):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.get_extent_for_project(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_engine.\
            get_layer_extent.assert_called_with(store_id='my-app:test_store',
                                                feature_name='app_users_resources_extent_test_resource_id')

    def test_create_extent_layer(self):
        sql = "SELECT id, name, description, ST_Transform(extent, 4326) as geometry FROM app_users_resources" \
              " WHERE id::text = 'test_resource_id'"
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.create_extent_layer(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_engine.create_sql_view_layer.\
            assert_called_with(store_id='my-app:test_store', default_style='atcore:resource_extent_layer_style',
                               layer_name='app_users_resources_extent_test_resource_id', geometry_type='Polygon',
                               sql=sql, srid=4326)

    @mock.patch('tethysext.atcore.services.resource_spatial_manager.ResourceSpatialManager.get_wms_endpoint')
    @mock.patch('tethysext.atcore.services.resource_spatial_manager.ResourceSpatialManager.get_extent_for_project')
    def test_get_resource_extent_wms_url(self, mock_get_extent, mock_wms_endpoint):
        geoserver_engine = mock.MagicMock()
        resource = mock.MagicMock()
        resource.id = 'resource_id'
        mock_get_extent.return_value = [-128.583984375, 22.1874049914, -64.423828125, 52.1065051908]
        mock_wms_endpoint.return_value = 'http://localhost/'
        spatial_manager = ResourceSpatialManager(geoserver_engine)
        wms_url = spatial_manager.get_resource_extent_wms_url(resource)
        expected_url = 'http://localhost/?service=WMS&version=1.1.0&request=GetMap&layers=' \
                       'my-app:app_users_resources_extent_resource_id&' \
                       'bbox=-128.583984375,22.1874049914,-64.423828125,52.1065051908&width=300&height=139&' \
                       'srs=EPSG:4326&format=image%2Fpng'
        self.assertEqual(expected_url, wms_url)

    @mock.patch('tethysext.atcore.services.resource_spatial_manager.ResourceSpatialManager.get_wms_endpoint')
    @mock.patch('tethysext.atcore.services.resource_spatial_manager.ResourceSpatialManager.get_extent_for_project')
    def test_get_resource_extent_wms_url_max_dim(self, mock_get_extent, mock_wms_endpoint):
        geoserver_engine = mock.MagicMock()
        resource = mock.MagicMock()
        resource.id = 'resource_id'
        mock_get_extent.return_value = [-68.583984375, 22.1874049914, -64.423828125, 52.1065051908]
        mock_wms_endpoint.return_value = 'http://localhost/'
        spatial_manager = ResourceSpatialManager(geoserver_engine)
        wms_url = spatial_manager.get_resource_extent_wms_url(resource)
        expected_url = 'http://localhost/?service=WMS&version=1.1.0&request=GetMap&' \
                       'layers=my-app:app_users_resources_extent_resource_id&' \
                       'bbox=-68.583984375,22.1874049914,-64.423828125,52.1065051908&' \
                       'width=41&height=300&srs=EPSG:4326&format=image%2Fpng'
        self.assertEqual(expected_url, wms_url)

    @mock.patch('tethysext.atcore.services.resource_spatial_manager.log')
    @mock.patch('tethysext.atcore.services.resource_spatial_manager.ResourceSpatialManager.get_extent_for_project')
    def test_get_resource_extent_wms_exception(self, mock_get_extent, mock_log):
        geoserver_engine = mock.MagicMock()
        resource = mock.MagicMock()
        resource.id = 'resource_id'
        mock_get_extent.side_effect = Exception
        spatial_manager = ResourceSpatialManager(geoserver_engine)
        spatial_manager.get_resource_extent_wms_url(resource)

        mock_log.exception.assert_called_with('An error occurred while trying to generate the preview image.')

    def test_create_extent_layer_value_error(self):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        self.assertRaises(ValueError, spatial_manager.create_extent_layer, 'dstore', 'rid', 'test_geotype', 1)

    def test_delete_extent_layer(self):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.delete_extent_layer(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_engine.delete_layer.\
            assert_called_with(layer_id='my-app:app_users_resources_extent_test_resource_id', datastore='test_store',
                               recurse=True)
