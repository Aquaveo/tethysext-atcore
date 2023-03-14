"""
********************************************************************************
* Name: manage_resources.py
* Author: Tanner and Teva
* Created On: December 17, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
from unittest import mock
from django.test import RequestFactory
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin, ResourceViewMixin
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users import AppUser, Resource
from django.core.handlers.wsgi import WSGIRequest
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.controllers.app_users.manage_resources import ManageResources
from tethysext.atcore.mixins.status_mixin import StatusMixin
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MockManageResources(ManageResources):
    _app = mock.MagicMock(namespace='foo')


class ManageResourcesTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()
        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()

        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )
        self.session.add(self.app_user)
        self.request_factory = RequestFactory()

        self.mock_members = mock.MagicMock()
        self.mock_client = mock.MagicMock()

        self.resource = Resource(
            name="test_organization"
        )

        self.session.add(self.resource)
        self.session.commit()

    @mock.patch.object(ManageResources, '_handle_get')
    def test_get(self, mock_handle_get):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # Call the function
        manage_resources = ManageResources()
        manage_resources.get(mock_request)

        # Test the function
        mock_handle_get.assert_called_with(mock_request)

    @mock.patch.object(ManageResources, '_handle_delete')
    def test_delete(self, mock_delete):
        mock_request = mock.MagicMock()
        mock_request.GET.get.side_effect = ['delete', '001']

        # call the method
        manage_resources = ManageResources()
        manage_resources.delete(mock_request)

        # test the results
        mock_delete.assert_called_with(mock_request, '001')

    def test_delete_not_delete(self):
        mock_request = mock.MagicMock()
        mock_request.GET.get.side_effect = ['post', '001']

        # call the method
        manage_resources = ManageResources()
        response = manage_resources.delete(mock_request)

        # test the results
        response_dict = json.loads(response._container[0].decode('utf-8'))
        self.assertFalse(response_dict['success'])
        self.assertEqual('Invalid action: post', response_dict['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.hasattr')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.render')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.paginate')
    @mock.patch.object(ManageResources, 'get_resource_action')
    @mock.patch.object(ManageResources, 'can_delete_resource')
    @mock.patch.object(ManageResources, 'can_edit_resource')
    @mock.patch.object(ManageResources, 'get_resources')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceViewMixin, 'get_resource_model')
    @mock.patch.object(AppUsersViewMixin, 'get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_handle_get(self, _, mock_app_user, __, mock_session_maker, mock_get_resources,
                        mock_can_edit, mock_can_delete, mock_get_resource_action, mock_paginate, mock_render,
                        mock_has_attr):

        session = mock_session_maker()()

        request_app_user = mock.MagicMock()
        mock_app_user().get_app_user_from_request.return_value = request_app_user

        mock_request = mock.MagicMock(spec=WSGIRequest)
        mock_request.user = self.django_user
        mock_request.GET.get.side_effect = [1, '15', 'date_created:']

        mock_get_resources.return_value = [self.resource]

        mock_can_edit.return_value = True

        mock_can_delete.return_value = True

        action_dcit = {
            'action': 'test_action',
            'title': 'test_title',
            'href': 'http://www.test.com'
        }

        mock_get_resource_action.return_value = action_dcit

        mock_has_attr.return_value = True

        mock_paginate.return_value = [mock.MagicMock(), mock.MagicMock()]

        # Call the function
        manage_resources = ManageResources()
        manage_resources._handle_get(mock_request)

        # test result
        update_settings_call_args = request_app_user.update_setting.call_args_list

        self.assertEqual('setting_resources-per-page', update_settings_call_args[0][1]['key'])
        self.assertEqual(session, update_settings_call_args[0][1]['session'])
        self.assertEqual('15', update_settings_call_args[0][1]['value'])
        self.assertEqual('resources', update_settings_call_args[0][1]['page'])

        self.assertEqual('setting_sort-resources-by', update_settings_call_args[1][1]['key'])
        self.assertEqual(session, update_settings_call_args[1][1]['session'])
        self.assertEqual('date_created:', update_settings_call_args[1][1]['value'])
        self.assertEqual('resources', update_settings_call_args[0][1]['page'])

        mock_get_resource_action.assert_called_with(session=session, request=mock_request,
                                                    request_app_user=request_app_user, resource=self.resource)

        paginate_call_args = mock_paginate.call_args_list

        self.assertEqual('test_organization', paginate_call_args[0][1]['objects'][0]['name'])
        self.assertEqual('http://www.test.com', paginate_call_args[0][1]['objects'][0]['action_href'])
        self.assertEqual('test_title', paginate_call_args[0][1]['objects'][0]['action_title'])
        self.assertEqual('test_action', paginate_call_args[0][1]['objects'][0]['action'])
        self.assertEqual(15, paginate_call_args[0][1]['results_per_page'])
        self.assertEqual(1, paginate_call_args[0][1]['page'])
        self.assertEqual('date_created:', paginate_call_args[0][1]['sort_by_raw'])
        self.assertFalse(paginate_call_args[0][1]['sort_reversed'])

        render_args = mock_render.call_args_list

        self.assertEqual(mock_request, render_args[0][0][0])
        self.assertEqual('atcore/app_users/manage_resources.html', render_args[0][0][1])
        self.assertEqual(mock_request, render_args[0][0][0])
        self.assertEqual('atcore/app_users/base.html', render_args[0][0][2]['base_template'])
        self.assertTrue(render_args[0][0][2]['show_new_button'])
        self.assertTrue(render_args[0][0][2]['show_users_link'])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.hasattr')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.render')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.paginate')
    @mock.patch.object(ManageResources, 'get_resource_action')
    @mock.patch.object(ManageResources, 'can_delete_resource')
    @mock.patch.object(ManageResources, 'can_edit_resource')
    @mock.patch.object(ManageResources, 'get_resources')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceViewMixin, 'get_resource_model')
    @mock.patch.object(AppUsersViewMixin, 'get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_handle_get_first_time(self, _, mock_app_user, __, mock_session_maker, mock_get_resources,
                                   mock_can_edit, mock_can_delete, mock_get_resource_action, mock_paginate, mock_render,
                                   mock_has_attr):

        session = mock_session_maker()()

        request_app_user = mock.MagicMock()
        request_app_user.get_setting.return_value = None
        mock_app_user().get_app_user_from_request.return_value = request_app_user

        mock_request = mock.MagicMock(spec=WSGIRequest)
        mock_request.user = self.django_user
        mock_request.GET.get.side_effect = [1, None, None]

        mock_get_resources.return_value = [self.resource]

        mock_can_edit.return_value = True

        mock_can_delete.return_value = True

        action_dcit = {
            'action': 'test_action',
            'title': 'test_title',
            'href': 'http://www.test.com'
        }

        mock_get_resource_action.return_value = action_dcit

        mock_has_attr.return_value = False

        mock_paginate.return_value = [mock.MagicMock(), mock.MagicMock()]

        # Call the function
        manage_resources = ManageResources()
        manage_resources._handle_get(mock_request)

        # test result
        update_settings_call_args = request_app_user.get_setting.call_args_list

        self.assertEqual('setting_resources-per-page', update_settings_call_args[0][1]['key'])
        self.assertEqual(session, update_settings_call_args[0][1]['session'])
        self.assertEqual('resources', update_settings_call_args[0][1]['page'])

        self.assertEqual('setting_sort-resources-by', update_settings_call_args[1][1]['key'])
        self.assertEqual(session, update_settings_call_args[1][1]['session'])
        self.assertEqual('resources', update_settings_call_args[0][1]['page'])

        mock_get_resource_action.assert_called_with(session=session, request=mock_request,
                                                    request_app_user=request_app_user, resource=self.resource)

        paginate_call_args = mock_paginate.call_args_list

        self.assertEqual('test_organization', paginate_call_args[0][1]['objects'][0]['name'])
        self.assertEqual('http://www.test.com', paginate_call_args[0][1]['objects'][0]['action_href'])
        self.assertEqual('test_title', paginate_call_args[0][1]['objects'][0]['action_title'])
        self.assertEqual('test_action', paginate_call_args[0][1]['objects'][0]['action'])
        self.assertEqual(10, paginate_call_args[0][1]['results_per_page'])
        self.assertEqual(1, paginate_call_args[0][1]['page'])
        self.assertEqual('date_created:reverse', paginate_call_args[0][1]['sort_by_raw'])
        self.assertTrue(paginate_call_args[0][1]['sort_reversed'])

        render_args = mock_render.call_args_list

        self.assertEqual(mock_request, render_args[0][0][0])
        self.assertEqual('atcore/app_users/manage_resources.html', render_args[0][0][1])
        self.assertEqual(mock_request, render_args[0][0][0])
        self.assertEqual('atcore/app_users/base.html', render_args[0][0][2]['base_template'])
        self.assertTrue(render_args[0][0][2]['show_new_button'])
        self.assertTrue(render_args[0][0][2]['show_users_link'])

    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch.object(ManageResources, 'perform_custom_delete_operations')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceViewMixin, 'get_resource_model')
    def test_handle_delete(self, _, mock_get_session, mock_custom_delete, __):
        session = mock_get_session()()
        mock_resource = mock.MagicMock()
        session.query().get.return_value = mock_resource

        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # Call the function
        manage_resources = ManageResources()
        ret = manage_resources._handle_delete(mock_request, '001')

        # test the results
        mock_custom_delete.assert_called_with(session, mock_request, mock_resource)
        session.delete.assert_called_with(mock_resource)
        session.commit.assert_called()
        session.close.assert_called()
        self.assertIn('{"success": true}', ret.content.decode('utf-8'))

    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch.object(ManageResources, 'perform_custom_delete_operations')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceViewMixin, 'get_resource_model')
    def test_handle_delete_query_exception(self, _, mock_get_session, mock_custom_delete, __):
        session = mock_get_session()()
        session.query().get.side_effect = Exception

        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # Call the function
        manage_resources = ManageResources()
        ret = manage_resources._handle_delete(mock_request, '001')

        # test the results
        mock_custom_delete.assert_not_called()
        session.delete.assert_not_called()
        session.commit.assert_not_called()
        session.close.assert_called()
        self.assertIn('"error": "Exception()"', ret.content.decode("utf-8"))
        self.assertIn('"success": false', ret.content.decode("utf-8"))

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.log')
    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch.object(ManageResources, 'perform_custom_delete_operations')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    @mock.patch.object(ResourceViewMixin, 'get_resource_model')
    def test_handle_delete_delete_exception(self, _, mock_get_session, mock_custom_delete, __, mock_log):
        session = mock_get_session()()
        mock_custom_delete.side_effect = Exception

        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # Call the function
        manage_resources = ManageResources()
        ret = manage_resources._handle_delete(mock_request, '001')

        # test the results
        mock_custom_delete.assert_called()
        session.delete.assert_called()
        session.commit.assert_called()
        session.close.assert_called()
        self.assertIn('"success": true', ret.content.decode("utf-8"))
        self.assertIn('Unable to perform custom delete operations on resource',
                      mock_log.exception.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.reverse')
    def test_get_resource_action_error(self, mock_reverse):
        mock_resource = mock.MagicMock()
        mock_resource.SLUG = "resources"
        mock_resource.ERROR_STATUSES = StatusMixin.ERROR_STATUSES
        mock_resource.get_status.return_value = 'Error'

        # Call the method
        manage_resources = MockManageResources()
        ret = manage_resources.get_resource_action('', '', '', mock_resource)

        mock_reverse.assert_called_with(
            f'{manage_resources._app.url_namespace}:{mock_resource.SLUG}_resource_details',
            args=[mock_resource.id]
        )
        self.assertDictEqual(
            {
                'action': ManageResources.ACTION_ERROR,
                'title': 'Error',
                'href': mock_reverse(),
            }, ret)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.reverse')
    def test_get_resource_action_working_status(self, mock_reverse):
        mock_resource = mock.MagicMock()
        mock_resource.id = 12345
        mock_resource.SLUG = "resources"
        mock_resource.WORKING_STATUSES = StatusMixin.WORKING_STATUSES
        mock_resource.get_status.return_value = 'Processing'

        mock_reverse.return_value = 'processing_url'

        # Call the method
        manage_resources = MockManageResources()
        manage_resources.get_app()
        ret = manage_resources.get_resource_action('', '', '', mock_resource)

        mock_reverse.assert_called_with(
            f'{manage_resources._app.url_namespace}:{mock_resource.SLUG}_resource_status'
        )
        self.assertDictEqual(
            {
                'action': ManageResources.ACTION_PROCESSING,
                'title': 'Processing',
                'href': 'processing_url?r=12345'
            }, ret)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.reverse')
    def test_get_resource_action_launch(self, mock_reverse):
        mock_resource = mock.MagicMock()
        mock_resource.SLUG = "resources"
        mock_resource.OK_STATUSES = StatusMixin.OK_STATUSES
        mock_resource.get_status.return_value = 'Available'

        # Call the method
        manage_resources = MockManageResources()
        manage_resources.get_app()
        ret = manage_resources.get_resource_action('', '', '', mock_resource)

        mock_reverse.assert_called_with(
            f'{manage_resources._app.url_namespace}:{mock_resource.SLUG}_resource_details',
            args=[mock_resource.id]
        )
        self.assertDictEqual(
            {
                'action': ManageResources.ACTION_LAUNCH,
                'title': ManageResources.default_action_title,
                'href': mock_reverse(),
            }, ret)

    def test_get_resources(self):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_session = mock.MagicMock()
        mock_request_app_user = mock.MagicMock()
        with mock.patch.object(ResourceViewMixin, 'get_resource_model') as mock_get_resource_model:
            mock_get_resource_model.return_value = 'resource_type'
            # Call the method
            manage_resources = ManageResources()
            manage_resources.get_resources(mock_session, mock_request, mock_request_app_user)

        # Test the results
        mock_request_app_user.get_resources.assert_called_with(mock_session, mock_request, of_type='resource_type',
                                                               include_children=False)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.has_permission')
    def test_can_edit_resource(self, mock_has_permission):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # call the method
        manage_resources = ManageResources()
        manage_resources.can_edit_resource('session', mock_request, 'resource')

        # test the results
        # resource and session are not needed and not used but requested
        mock_has_permission.assert_called_with(mock_request, 'edit_resource')

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.has_permission')
    def test_can_delete_resource(self, mock_has_permission):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # call the method
        manage_resources = ManageResources()
        manage_resources.can_delete_resource('session', mock_request, 'resource')

        # test the results
        # resource and session are not needed and not used but requested
        mock_has_permission.assert_called_with(mock_request, 'delete_resource')

    @mock.patch('tethysext.atcore.controllers.app_users.manage_resources.has_permission')
    def test_can_delete_resource_always(self, mock_has_permission):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        mock_has_permission.side_effect = [False, True]
        # call the method
        manage_resources = ManageResources()
        manage_resources.can_delete_resource('session', mock_request, 'resource')

        # test the results
        # resource and session are not needed and not used but requested
        call_args = mock_has_permission.call_args_list
        self.assertEqual('delete_resource', call_args[0][0][1])
        self.assertEqual(mock_request, call_args[0][0][0])
        self.assertEqual('always_delete_resource', call_args[1][0][1])
        self.assertEqual(mock_request, call_args[1][0][0])

    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    def test_perform_custom_delete_operations(self, mock_get_session):
        session = mock_get_session()()
        mock_request = self.request_factory.get('/foo/bar/')

        ManageResources().perform_custom_delete_operations(session, mock_request, self.resource)
