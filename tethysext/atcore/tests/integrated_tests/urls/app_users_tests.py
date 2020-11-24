from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.models.app_users import AppUser, Resource, Organization
from tethysext.atcore.urls import app_users
from tethysext.atcore.controllers.app_users import ManageUsers, ModifyUser, AddExistingUser, UserAccount, \
    ModifyOrganization, ManageOrganizationMembers, ManageOrganizations
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.tests.mock.url_map_maker import MockUrlMapMaker


class CustomAppUser(AppUser):
    pass


class CustomOrganization(Organization):
    pass


class CustomResource(Resource):
    pass


class CustomManageUsers(ManageUsers):
    pass


class CustomModifyUser(ModifyUser):
    pass


class CustomAddExistingUser(AddExistingUser):
    pass


class CustomManageOrganizations(ManageOrganizations):
    pass


class CustomModifyOrganization(ModifyOrganization):
    pass


class CustomManageOrganizationMembers(ManageOrganizationMembers):
    pass


class CustomUserAccount(UserAccount):
    pass


class CustomPermissionsManager(AppPermissionsManager):
    pass


class InvalidController:
    pass


class InvalidPermissionsManager:
    pass


class AppUserUrlsTests(TethysTestCase):

    def setUp(self):
        self.base_url_path = 'foo/bar'
        self.names = ['app_users_manage_users', 'app_users_add_user', 'app_users_edit_user',
                      'app_users_add_existing_user', 'app_users_manage_organizations',
                      'app_users_manage_organization_members', 'app_users_new_organization',
                      'app_users_edit_organization', 'app_users_user_account',
                      'resources_manage_resources', 'resources_new_resource', 'resources_edit_resource',
                      'resources_resource_details', 'resources_resource_status']
        self.urls = ['users', 'users/new', 'users/{user_id}/edit', 'users/add-existing', 'organizations',
                     'organizations/{organization_id}/members', 'organizations/new',
                     'organizations/{organization_id}/edit', 'users/me',
                     Resource.DISPLAY_TYPE_PLURAL.lower(), Resource.DISPLAY_TYPE_PLURAL.lower() + '/new',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/{resource_id}/edit',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/{resource_id}/details',
                     Resource.DISPLAY_TYPE_PLURAL.lower() + '/status']
        self.num_urls = 14

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
        url_maps = app_users.urls(MockUrlMapMaker, None, None)

        self.name_asserts(url_maps)
        self.assertEqual(len(url_maps), self.num_urls)
        self.name_asserts(url_maps)
        self.url_asserts(url_maps)

    def test_base_url_path(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, base_url_path=self.base_url_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_startswith_slash(self):
        startswith_path = '/' + self.base_url_path
        url_maps = app_users.urls(MockUrlMapMaker, None, None, base_url_path=startswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_endswith_slash(self):
        endswith_path = self.base_url_path + '/'
        url_maps = app_users.urls(MockUrlMapMaker, None, None, base_url_path=endswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_custom_manage_users_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomManageUsers])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_manage_users'], ManageUsers, CustomManageUsers)

    def test_custom_modify_user_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomModifyUser])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_add_user', 'app_users_edit_user'], ModifyUser, CustomModifyUser)

    def test_custom_add_existing_user_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomAddExistingUser])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_add_existing_user'], AddExistingUser, CustomAddExistingUser)

    def test_custom_user_account_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomUserAccount])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_user_account'], UserAccount, CustomUserAccount)

    def test_custom_manage_organizations_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomManageOrganizations])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_manage_organizations'], ManageOrganizations, CustomManageOrganizations)  # noqa: E501

    def test_custom_modify_organizations_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomModifyOrganization])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_new_organization', 'app_users_edit_organization'], ModifyOrganization, CustomModifyOrganization)  # noqa: E501

    def test_custom_manage_organization_members_controller(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomManageOrganizationMembers])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(
            url_maps,
            ['app_users_manage_organization_members'],
            ManageOrganizationMembers, CustomManageOrganizationMembers
        )

    def test_invalid_controller_arg_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=[InvalidController])

    def test_invalid_controller_arg_not_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=['not-a-class'])

    def test_custom_permissions_manager(self):
        url_maps = app_users.urls(MockUrlMapMaker, None, None, custom_permissions_manager=CustomPermissionsManager)
        self.assertEqual(len(url_maps), self.num_urls)

        for url_map in url_maps:
            _PermissionsManager = url_map.controller.view_initkwargs['_PermissionsManager']
            self.assertEqual(CustomPermissionsManager, _PermissionsManager)

    def test_invalid_custom_permissions_manager_not_a_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_permissions_manager='not-a-class')

    def test_invalid_custom_permissions_manager_not_permissions_manager(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_permissions_manager=InvalidPermissionsManager)

    def test_custom_base_url_path_and_models(self):
        mockapp = object()
        mock_db_name = "foo"
        url_maps = app_users.urls(MockUrlMapMaker, mockapp, mock_db_name, base_url_path=self.base_url_path,
                                  custom_controllers=[CustomManageUsers, CustomModifyUser, CustomAddExistingUser])
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)
        self.controller_asserts(url_maps, ['app_users_manage_users'], ManageUsers, CustomManageUsers)
        self.controller_asserts(url_maps, ['app_users_add_user', 'app_users_edit_user'], ModifyUser, CustomModifyUser)
        self.controller_asserts(url_maps, ['app_users_add_existing_user'], AddExistingUser, CustomAddExistingUser)

    def test_custom_models(self):
        # NOTE: Don't know how to validate this... for not just test that it doesn't throw an error.
        mockapp = object()
        mock_db_name = "foo"
        app_users.urls(MockUrlMapMaker, mockapp, mock_db_name, custom_models=[CustomAppUser])
        app_users.urls(MockUrlMapMaker, mockapp, mock_db_name, custom_models=[CustomOrganization])
        app_users.urls(MockUrlMapMaker, mockapp, mock_db_name, custom_models=[CustomResource])
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_models=['invalid-model'])
