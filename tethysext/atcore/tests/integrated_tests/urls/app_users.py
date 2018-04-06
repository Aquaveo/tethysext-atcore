from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.urls import app_users
from tethysext.atcore.controllers.app_users import ManageUsers, ModifyUser, AddExistingUser


class MockUrlMapMaker:
    """
    Mock the UrlMap meta class for testing.
    """
    def __init__(self, name, url, controller):
        self.name = name
        self.url = url
        self.controller = controller


class CustomManageUsers(ManageUsers):
    pass


class CustomModifyUser(ModifyUser):
    pass


class CustomAddExistingUser(AddExistingUser):
    pass


class InvalidController:
    pass


class AppUserUrlsTests(TethysTestCase):

    def setUp(self):
        self.base_url_path = 'foo/bar'
        self.names = ['app_users_manage_users', 'app_users_add_user', 'app_users_edit_user',
                      'app_users_add_existing_user', 'app_users_manage_organizations',
                      'app_users_manage_organization_members', 'app_users_new_organization',
                      'app_users_edit_organization']
        self.urls = ['users', 'users/new', 'users/{user_id}/edit', 'users/add-existing', 'organizations',
                     'organizations/{organization_id}/members', 'organizations/new',
                     'organizations/{organization_id}/edit']
        self.num_urls = 8

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
        url_maps = app_users.urls(MockUrlMapMaker)

        self.name_asserts(url_maps)
        self.assertEqual(len(url_maps), self.num_urls)
        self.name_asserts(url_maps)
        self.url_asserts(url_maps)

    def test_base_url_path(self):
        url_maps = app_users.urls(MockUrlMapMaker, base_url_path=self.base_url_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_startswith_slash(self):
        startswith_path = '/' + self.base_url_path
        url_maps = app_users.urls(MockUrlMapMaker, base_url_path=startswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_endswith_slash(self):
        endswith_path = self.base_url_path + '/'
        url_maps = app_users.urls(MockUrlMapMaker, base_url_path=endswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_custom_manage_users_model(self):
        url_maps = app_users.urls(MockUrlMapMaker, CustomManageUsers)
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_manage_users'], ManageUsers, CustomManageUsers)

    def test_custom_modify_user_model(self):
        url_maps = app_users.urls(MockUrlMapMaker, CustomModifyUser)
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_add_user', 'app_users_edit_user'], ModifyUser, CustomModifyUser)

    def test_custom_add_existing_user_model(self):
        url_maps = app_users.urls(MockUrlMapMaker, CustomAddExistingUser)
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['app_users_add_existing_user'], AddExistingUser, CustomAddExistingUser)

    def test_invalid_controller_arg_class(self):
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, InvalidController)

    def test_invalid_controller_arg_not_class(self):
        self.assertRaises(ValueError, app_users.urls, MockUrlMapMaker, 'not-a-class')

    def test_custom_base_url_path_and_models(self):
        url_maps = app_users.urls(
            MockUrlMapMaker,
            CustomManageUsers,
            CustomModifyUser,
            CustomAddExistingUser,
            base_url_path=self.base_url_path
        )
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)
        self.controller_asserts(url_maps, ['app_users_manage_users'], ManageUsers, CustomManageUsers)
        self.controller_asserts(url_maps, ['app_users_add_user', 'app_users_edit_user'], ModifyUser, CustomModifyUser)
        self.controller_asserts(url_maps, ['app_users_add_existing_user'], AddExistingUser, CustomAddExistingUser)
