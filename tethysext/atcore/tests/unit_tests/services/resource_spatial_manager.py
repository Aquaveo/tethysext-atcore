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

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_get_extent_for_project(self, _):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.get_extent_for_project(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_api.\
            get_layer_extent.assert_called_with(datastore_name='test_store',
                                                feature_name='app_users_resources_extent_test_resource_id',
                                                workspace='my-app')

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_create_extent_layer(self, _):
        sql = "SELECT id, name, description, ST_Transform(extent, 4326) as geometry FROM app_users_resources" \
              " WHERE id::text = 'test_resource_id'"
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.create_extent_layer(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_api.create_layer.\
            assert_called_with(datastore_name='test_store', default_style='atcore:resource_extent_layer_style',
                               feature_name='app_users_resources_extent_test_resource_id', geometry_type='Polygon',
                               sql=sql, srid=4326, workspace='my-app')

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_create_extent_layer_value_error(self, _):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        self.assertRaises(ValueError, spatial_manager.create_extent_layer, 'dstore', 'rid', 'test_geotype', 1)

    @mock.patch('tethysext.atcore.services.base_spatial_manager.GeoServerAPI')
    def test_delete_extent_layer(self, _):
        spatial_manager = ResourceSpatialManager(self.geoserver_engine)
        spatial_manager.delete_extent_layer(datastore_name=self.datastore_name, resource_id=self.resource_id)
        spatial_manager.gs_api.delete_layer.\
            assert_called_with(workspace='my-app', datastore_name='test_store',
                               name='app_users_resources_extent_test_resource_id', recurse=True)
