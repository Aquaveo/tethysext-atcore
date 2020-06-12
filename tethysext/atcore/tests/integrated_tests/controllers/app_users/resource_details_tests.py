"""
********************************************************************************
* Name: resource_details_tests.py
* Author: mlebaron
* Created On: October 2, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.models import User
from django.test import RequestFactory
from tethysext.atcore.controllers.app_users.resource_details import ResourceDetails
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceDetailsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.rd = ResourceDetails()
        staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.user = staff_user
        self.request_factory = RequestFactory()
        self.resource_id = '624ceaca-22dd-42fd-9f9d-7517844514b8'

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.ResourceDetails.default_back_url')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.render')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethys_apps.decorators.has_permission')
    def test_get(self, mock_has_permission, mock_get_sessionmaker, _, mock_back_url):
        mock_has_permission.return_value = True
        mock_get_sessionmaker.return_value = mock.MagicMock()
        mock_back_url.return_value = '/back/url'

        self.request.method = 'get'
        controller = ResourceDetails.as_controller()

        ret = controller(self.request)

        render_args = ret._mock_new_parent.call_args[0]
        self.assertEqual(self.request, render_args[0])
        self.assertEqual('atcore/app_users/resource_details.html', render_args[1])
        self.assertEqual(None, render_args[2]['resource'])
        self.assertEqual(mock_back_url.return_value, render_args[2]['back_url'])
        self.assertEqual('atcore/app_users/base.html', render_args[2]['base_template'])

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.get_active_app')
    def test_default_back_url_with_back(self, mock_get_active_app, mock_reverse):
        namespace = 'app_namespace'
        mock_get_active_app.return_value = mock.MagicMock(namespace=namespace)
        self.request.GET = {'back': 'manage-organizations'}

        back = self.rd.default_back_url(self.request)

        self.assertEqual('app_namespace:app_users_manage_organizations', back._mock_new_parent.call_args[0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.get_active_app')
    def test_default_back_url_without_back(self, mock_get_active_app, mock_reverse):
        namespace = 'app_namespace'
        mock_get_active_app.return_value = mock.MagicMock(namespace=namespace)
        self.request.GET = {}

        back = self.rd.default_back_url(self.request)

        self.assertEqual('app_namespace:app_users_manage_resources', back._mock_new_parent.call_args[0][0])

    def test_get_context(self):
        context = {'success': True}

        ret = self.rd.get_context(self.request, context)

        self.assertTrue(ret['success'])

    def test_post(self):
        post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'ham'}
        request = self.request_factory.post('/foo/bar/', data=post_data)
        self.rd._handle_new_workflow_form = mock.MagicMock()

        ret = self.rd.post(request, self.resource_id)

        self.rd._handle_new_workflow_form.assert_called()
        self.assertEqual(self.rd._handle_new_workflow_form(), ret)

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    def test_post_invalid_form(self, mock_messages):
        post_data = {'bad-data': ''}
        request = self.request_factory.post('/foo/bar/', data=post_data)
        self.rd._handle_new_workflow_form = mock.MagicMock()
        self.rd.get = mock.MagicMock()

        ret = self.rd.post(request, self.resource_id)

        self.rd._handle_new_workflow_form.assert_not_called()
        self.rd.get.assert_called_with(request, self.resource_id)
        self.assertEqual(self.rd.get(), ret)
        mock_messages.warning.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    def test__handle_new_workflow_form_valid(self, mock_messages):
        # TODO: Fix test
        pass
        # post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'ham'}
        # request = self.request_factory.post('/foo/bar/', data=post_data)
        # self.rd.get = mock.MagicMock()
        # self.rd.get_app_user_model = mock.MagicMock()
        # self.rd.get_sessionmaker = mock.MagicMock()
        # mock_session = self.rd.get_sessionmaker()()
        # ret = self.rd._handle_new_workflow_form(request, self.resource_id, post_data)
        #
        # self.assertEqual(self.rd.get(), ret)
        # mock_session.close.assert_called()
        # mock_messages.success.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    def test__handle_new_workflow_form_no_name(self, mock_messages):
        # TODO: Fix test
        pass
        # post_data = {'new-workflow': '', 'workflow-name': '', 'workflow-type': 'ham'}
        # request = self.request_factory.post('/foo/bar/', data=post_data)
        # self.rd.get = mock.MagicMock()
        # self.rd.get_app_user_model = mock.MagicMock()
        # self.rd.get_sessionmaker = mock.MagicMock()

        # ret = self.rd._handle_new_workflow_form(request, self.resource_id, post_data)

        # self.assertEqual(self.rd.get(), ret)
        # mock_messages.error.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    def test__handle_new_workflow_form_no_type(self, mock_messages):
        post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': ''}
        request = self.request_factory.post('/foo/bar/', data=post_data)
        self.rd.get = mock.MagicMock()
        self.rd.get_app_user_model = mock.MagicMock()
        self.rd.get_sessionmaker = mock.MagicMock()

        ret = self.rd._handle_new_workflow_form(request, self.resource_id, post_data)

        self.assertEqual(self.rd.get(), ret)
        mock_messages.error.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.log')
    def test__handle_new_workflow_form_invalid_type(self, _, mock_messages):
        # TODO: Fix test
        pass
        # post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'fram'}
        # request = self.request_factory.post('/foo/bar/', data=post_data)
        # self.rd.get = mock.MagicMock()
        # self.rd.get_app_user_model = mock.MagicMock()
        # self.rd.get_sessionmaker = mock.MagicMock()
        #
        # ret = self.rd._handle_new_workflow_form(request, self.resource_id, post_data)
        #
        # self.assertEqual(self.rd.get(), ret)
        # mock_messages.error.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.log')
    def test__handle_new_workflow_form_exception(self, mock_log, mock_messages):
        # TODO: Fix test
        pass
        # post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'ham'}
        # request = self.request_factory.post('/foo/bar/', data=post_data)
        # self.rd.get = mock.MagicMock()
        # self.rd.get_app_user_model = mock.MagicMock()
        # self.rd.get_sessionmaker = mock.MagicMock()
        # mock_session = self.rd.get_sessionmaker()()
        # mock_session.add.side_effect = Exception
        #
        # ret = self.rd._handle_new_workflow_form(request, self.resource_id, post_data)
        #
        # self.assertEqual(self.rd.get(), ret)
        # mock_log.exception.assert_called()
        # mock_session.close.assert_called()
        # mock_messages.error.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.log')
    def test_delete(self, mock_log):
        post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'ham'}
        request = self.request_factory.post('/foo/bar/', data=post_data)
        self.rd._handle_new_workflow_form = mock.MagicMock()

        self.rd.get_sessionmaker = mock.MagicMock()
        mock_session = self.rd.get_sessionmaker()()

        ret = self.rd.delete(request, self.resource_id)

        mock_session.delete.assert_called()
        mock_session.close.assert_called()

        self.assertIsInstance(ret, JsonResponse)

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.log')
    def test_delete_exception(self, mock_log):
        post_data = {'new-workflow': '', 'workflow-name': 'spam', 'workflow-type': 'ham'}
        request = self.request_factory.post('/foo/bar/', data=post_data)
        self.rd._handle_new_workflow_form = mock.MagicMock()

        self.rd.get_sessionmaker = mock.MagicMock()
        mock_session = self.rd.get_sessionmaker()()
        mock_session.query().get.side_effect = Exception

        ret = self.rd.delete(request, self.resource_id)

        mock_session.close.assert_called()
        mock_log.exception.assert_called_with('An error occurred while attempting to delete a workflow.')
        self.assertIsInstance(ret, JsonResponse)
