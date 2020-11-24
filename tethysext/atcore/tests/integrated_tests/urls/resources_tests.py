from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.urls import resources
from tethysext.atcore.controllers.app_users import ManageResources, ModifyResource, ResourceDetails, ResourceStatus
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.tests.mock.url_map_maker import MockUrlMapMaker


class CustomResource(Resource):
    pass


class CustomManageResources(ManageResources):
    pass


class CustomModifyResource(ModifyResource):
    pass


class CustomResourceDetails(ResourceDetails):
    pass


class CustomResourceStatus(ResourceStatus):
    pass


class CustomPermissionsManager(AppPermissionsManager):
    pass


class InvalidController:
    pass


class InvalidPermissionsManager:
    pass


class ResourceUrlsTests(TethysTestCase):

    def setUp(self):
        self.base_url_path = 'foo/bar'
        self.names = ['resources_manage_resources', 'resources_new_resource', 'resources_edit_resource',
                      'resources_resource_details', 'resources_resource_status']
        self.urls = [Resource.DISPLAY_TYPE_PLURAL.lower(), Resource.DISPLAY_TYPE_PLURAL.lower() + '/new',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/{resource_id}/edit',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/{resource_id}/details',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/status']
        self.num_urls = 5

    def tearDown(self):
        pass

    def name_asserts(self, url_maps):
        for url_map in url_maps:
            name = url_map.name
            self.assertIn(name, self.names)

    def url_asserts(self, url_maps, with_base_url=False):
        if with_base_url:
            compare_urls = [self.base_url_path + '/' + u for u in self.urls]
        else:
            compare_urls = self.urls

        for url_map in url_maps:
            url = url_map.url
            self.assertIn(url, compare_urls)

    def controller_asserts(self, url_maps, controller_names, default_controller, custom_controller):
        num_controllers_tested = 0

        for url_map in url_maps:
            if url_map.name in controller_names:
                controller = url_map.controller
                self.assertTrue(callable(controller))
                self.assertNotEqual(default_controller.as_controller().__name__, controller.__name__)
                self.assertEqual(custom_controller.as_controller().__name__, controller.__name__)
                num_controllers_tested += 1

        self.assertEqual(len(controller_names), num_controllers_tested)

    def test_vanilla(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None)

        self.name_asserts(url_maps)
        self.assertEqual(len(url_maps), self.num_urls)
        self.name_asserts(url_maps)
        self.url_asserts(url_maps)

    def test_base_url_path(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, base_url_path=self.base_url_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_startswith_slash(self):
        startswith_path = '/' + self.base_url_path
        url_maps = resources.urls(MockUrlMapMaker, None, None, base_url_path=startswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_endswith_slash(self):
        endswith_path = self.base_url_path + '/'
        url_maps = resources.urls(MockUrlMapMaker, None, None, base_url_path=endswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_custom_manage_resources_controller(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomManageResources])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['resources_manage_resources'], ManageResources, CustomManageResources)

    def test_custom_modify_resource_controller(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomModifyResource])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(
            url_maps,
            ['resources_new_resource', 'resources_edit_resource'],
            ModifyResource,
            CustomModifyResource
        )

    def test_custom_resource_details_controller(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomResourceDetails])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['resources_resource_details'], ResourceDetails, CustomResourceDetails)

    def test_custom_resource_status_controller(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomResourceStatus])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['resources_resource_status'], ResourceStatus, CustomResourceStatus)

    def test_invalid_controller_arg_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, resources.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=[InvalidController])

    def test_invalid_controller_arg_not_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, resources.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=['not-a-class'])

    def test_custom_permissions_manager(self):
        url_maps = resources.urls(MockUrlMapMaker, None, None, custom_permissions_manager=CustomPermissionsManager)
        self.assertEqual(len(url_maps), self.num_urls)

        for url_map in url_maps:
            _PermissionsManager = url_map.controller.view_initkwargs['_PermissionsManager']
            self.assertEqual(CustomPermissionsManager, _PermissionsManager)

    def test_invalid_custom_permissions_manager_not_a_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, resources.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_permissions_manager='not-a-class')

    def test_invalid_custom_permissions_manager_not_permissions_manager(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, resources.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_permissions_manager=InvalidPermissionsManager)

    def test_custom_base_url_path_and_models(self):
        mockapp = object()
        mock_db_name = "foo"
        url_maps = resources.urls(
            MockUrlMapMaker, mockapp, mock_db_name, base_url_path=self.base_url_path,
            custom_controllers=[CustomManageResources, CustomModifyResource, CustomResourceDetails,
                                CustomResourceStatus]
        )
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)
        self.controller_asserts(url_maps, ['resources_manage_resources'], ManageResources, CustomManageResources)
        self.controller_asserts(
            url_maps, ['resources_new_resource', 'resources_edit_resource'], ModifyResource, CustomModifyResource
        )
        self.controller_asserts(url_maps, ['resources_resource_details'], ResourceDetails, CustomResourceDetails)
        self.controller_asserts(url_maps, ['resources_resource_status'], ResourceStatus, CustomResourceStatus)

    def test_custom_models(self):
        # NOTE: Don't know how to validate this... for not just test that it doesn't throw an error.
        mockapp = object()
        mock_db_name = "foo"
        resources.urls(MockUrlMapMaker, mockapp, mock_db_name, custom_models=[CustomResource])
        self.assertRaises(ValueError, resources.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_models=['invalid-model'])
