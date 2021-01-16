"""
********************************************************************************
* Name: manage_users_tests.py
* Author: mlebaron
* Created On: October 14, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import json
import sys
from unittest import mock
from django.http import HttpRequest
from django.contrib.auth.models import User
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.controllers.app_users.manage_users import ManageUsers
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ManageUsersTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()

        self.admin_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )

        self.staff_user = User.objects.create_superuser(
            username='bar',
            email='foo1@bar.com',
            password='pass'
        )
        self.app_user = User.objects.create_user(
            username='foobar',
            email='foo2@bar.com',
            password='pass'
        )

        self.request = mock.MagicMock(spec=HttpRequest, user=self.admin_user)

        self.controller = ManageUsers.as_controller()

        decorator_has_permission_patcher = mock.patch('tethys_apps.decorators.has_permission')
        self.mock_has_decorator_permission = decorator_has_permission_patcher.start()
        self.mock_has_decorator_permission.return_value = True
        self.addCleanup(decorator_has_permission_patcher.stop)

        user_has_permission_patcher = mock.patch('tethysext.atcore.controllers.app_users.manage_users.has_permission')
        self.mock_user_has_permission = user_has_permission_patcher.start()
        self.mock_user_has_permission.return_value = True
        self.addCleanup(user_has_permission_patcher.stop)

        mixins_has_permission_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.has_permission')
        self.mock_mixins_has_permission = mixins_has_permission_patcher.start()
        self.mock_mixins_has_permission.return_value = True
        self.addCleanup(mixins_has_permission_patcher.stop)

        user_get_permission_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')  # noqa: E501
        self.mock_user_get_permission = user_get_permission_patcher.start()
        self.mock_user_get_permission.return_value = True
        self.addCleanup(user_get_permission_patcher.stop)

        get_session_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')  # noqa: E501
        self.mock_get_session = get_session_patcher.start()
        self.addCleanup(get_session_patcher.stop)

        get_active_app_patcher = mock.patch('tethys_apps.utilities.get_active_app')
        self.mock_get_active_app = get_active_app_patcher.start()
        self.addCleanup(get_active_app_patcher.stop)

        render_patcher = mock.patch('tethysext.atcore.controllers.app_users.manage_users.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_get(self):
        self.request.method = 'get'
        self.request.GET = {'page': '2', 'show': '20'}

        self.controller(self.request)

        self.assertEqual(self.request, self.mock_render.call_args[0][0])
        self.assertEqual('atcore/app_users/manage_users.html', self.mock_render.call_args[0][1])

        context = self.mock_render.call_args[0][2]
        self.assertTrue(context['is_app_admin'])
        self.assertEqual('User Accounts', context['page_title'])
        self.assertEqual('atcore/app_users/base.html', context['base_template'])
        self.assertEqual([], context['user_cards'])
        self.assertTrue(context['show_new_button'])
        self.assertTrue(context['show_action_buttons'])
        self.assertTrue(context['show_links_to_organizations'])
        self.assertEqual(0, context['pagination_info']['num_results'])
        self.assertEqual('users', context['pagination_info']['result_name'])
        self.assertEqual(1, context['pagination_info']['page'])
        self.assertEqual(0, context['pagination_info']['min_showing'])
        self.assertEqual(0, context['pagination_info']['max_showing'])
        self.assertEqual(2, context['pagination_info']['next_page'])
        self.assertEqual(0, context['pagination_info']['previous_page'])
        self.assertEqual(None, context['pagination_info']['sort_by'])
        self.assertFalse(context['pagination_info']['sort_reversed'])
        self.assertFalse(context['pagination_info']['enable_next_button'])
        self.assertFalse(context['pagination_info']['enable_previous_button'])
        self.assertTrue(context['pagination_info']['hide_buttons'])
        self.assertTrue(context['pagination_info']['hide_header_buttons'])
        self.assertEqual(20, context['pagination_info']['show'])
        self.assertEqual([], context['pagination_info']['results_per_page_options'])
        self.assertTrue(context['pagination_info']['hide_results_per_page_options'])

    @mock.patch('tethysext.atcore.models.app_users.app_user.AppUser.get_display_name')
    @mock.patch('tethysext.atcore.models.app_users.app_user.AppUser.get_app_user_from_request')
    @mock.patch('tethysext.atcore.models.app_users.app_user.AppUser.get_rank')
    def test_get_staff_user(self, mock_get_rank, mock_get_app_user, mock_get_display_name):
        mock_get_rank.return_value = 1
        mock_get_display_name.return_value = 'my name'
        app_user = mock.MagicMock(username=self.admin_user.username)
        app_user.is_staff.return_value = False
        staff_user = mock.MagicMock(username='aaaa')
        staff_user.is_staff.return_value = True
        non_staff_user = mock.MagicMock(username=self.admin_user.username)
        non_staff_user.is_staff.return_value = False
        non_staff_user.get_rank.return_value = 100
        app_user.get_peers.return_value = [staff_user, non_staff_user]
        app_user.get_rank.return_value = 2
        app_user.name = self.admin_user.username
        mock_get_app_user.return_value = app_user
        self.request.method = 'get'
        self.request.user = self.admin_user
        self.request.GET = {}
        self.mock_user_has_permission.return_value = False

        self.controller(self.request)

        self.assertEqual(self.request, self.mock_render.call_args[0][0])
        self.assertEqual('atcore/app_users/manage_users.html', self.mock_render.call_args[0][1])

        context = self.mock_render.call_args[0][2]
        self.assertTrue(context['is_app_admin'])
        self.assertEqual('User Accounts', context['page_title'])
        self.assertEqual('atcore/app_users/base.html', context['base_template'])
        self.assertIn('id', context['user_cards'][0])
        self.assertIn('username', context['user_cards'][0])
        self.assertEqual('Me', context['user_cards'][0]['fullname'])
        self.assertIn('email', context['user_cards'][0])
        self.assertIn('active', context['user_cards'][0])
        self.assertIn('role', context['user_cards'][0])
        self.assertIn('organizations', context['user_cards'][0])
        self.assertTrue(context['user_cards'][0]['editable'])
        self.assertFalse(context['show_new_button'])
        self.assertFalse(context['show_action_buttons'])
        self.assertTrue(context['show_remove_button'])
        self.assertTrue(context['show_add_existing_button'])
        self.assertTrue(context['show_remove_button'])
        self.assertTrue(context['show_add_existing_button'])
        self.assertFalse(context['show_links_to_organizations'])
        self.assertEqual(2, context['pagination_info']['num_results'])
        self.assertEqual('users', context['pagination_info']['result_name'])
        self.assertEqual(1, context['pagination_info']['page'])
        self.assertEqual(1, context['pagination_info']['min_showing'])
        self.assertEqual(2, context['pagination_info']['max_showing'])
        self.assertEqual(2, context['pagination_info']['next_page'])
        self.assertEqual(0, context['pagination_info']['previous_page'])
        self.assertEqual(None, context['pagination_info']['sort_by'])
        self.assertFalse(context['pagination_info']['sort_reversed'])
        self.assertFalse(context['pagination_info']['enable_next_button'])
        self.assertFalse(context['pagination_info']['enable_previous_button'])
        self.assertTrue(context['pagination_info']['hide_buttons'])
        self.assertTrue(context['pagination_info']['hide_header_buttons'])
        self.assertEqual(10, context['pagination_info']['show'])
        self.assertEqual([], context['pagination_info']['results_per_page_options'])
        self.assertTrue(context['pagination_info']['hide_results_per_page_options'])
        self.assertFalse(context['show_users_link'])
        self.assertFalse(context['show_resources_link'])
        self.assertFalse(context['show_organizations_link'])

    def test_delete_delete(self):
        self.request.GET = {'action': 'delete', 'id': 123456}
        self.request.method = 'delete'

        response = self.controller(self.request)

        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertTrue(response_dict['success'])
        self.assertNotIn('error', response_dict)

    def test_delete_delete_exception(self):
        self.request.GET = {'action': 'delete', 'id': 123456}
        self.request.method = 'delete'
        self.mock_get_session()().query.side_effect = Exception('Some exception message')

        response = self.controller(self.request)

        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertFalse(response_dict['success'])
        if sys.version_info.minor <= 6:
            self.assertEqual("Exception('Some exception message',)", response_dict['error'])
        else:
            self.assertEqual("Exception('Some exception message')", response_dict['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_delete_remove(self, _):
        self.request.GET = {'action': 'remove'}
        self.request.method = 'delete'

        response = self.controller(self.request)

        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertTrue(response_dict['success'])
        self.assertNotIn('error', response_dict)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    def test_delete_remove_exception(self, mock_manager):
        manager = mock.MagicMock(spec=AppPermissionsManager, name='matt')
        manager.remove_all_permissions_groups.side_effect = Exception('Some exception message')
        mock_manager.return_value = manager
        self.request.GET = {'action': 'remove'}
        self.request.method = 'delete'

        response = self.controller(self.request)

        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertFalse(response_dict['success'])
        if sys.version_info.minor <= 6:
            self.assertEqual("Exception('Some exception message',)", response_dict['error'])
        else:
            self.assertEqual("Exception('Some exception message')", response_dict['error'])

    def test_delete_unknown_action(self):
        self.request.GET = {'action': 'swim'}
        self.request.method = 'delete'

        response = self.controller(self.request)

        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertFalse(response_dict['success'])
        self.assertEqual('Invalid action: swim', response_dict['error'])
