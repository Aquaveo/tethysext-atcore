"""
********************************************************************************
* Name: decorators.py
* Author: nswain
* Created On: May 16, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
from unittest import mock
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect
from sqlalchemy.orm.session import sessionmaker
from django.test import RequestFactory
from sqlalchemy.exc import StatementError
from tethysext.atcore.exceptions import ATCoreException
from sqlalchemy.orm.exc import NoResultFound
from tethys_apps.base.controller import TethysController
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.services.app_users.decorators import resource_controller
from tethysext.atcore.tests.factories.django_user import UserFactory
from django.test.utils import override_settings

from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MockController(TethysController):
    sessionmaker = None

    def get_app_user_model(self):
        return AppUser

    def get_sessionmaker(self):
        return self.sessionmaker

    @active_user_required()
    def get(self, *args, **kwargs):
        return 'SUCCESS'


class MockResourceController(TethysController):
    sessionmaker = mock.MagicMock()
    resource = mock.MagicMock(DISPLAY_TYPE_SINGULAR='Generic Resource')
    back_url = '/back/url'

    def get_sessionmaker(self):
        return self.sessionmaker

    def get_resource_model(self):
        return self.resource

    @resource_controller()
    def get(self, request, *args, **kwargs):
        return 'SUCCESS'

    @resource_controller()
    def raise_value_error(self, *args, **kwargs):
        raise ValueError('This is the ValueError')

    @resource_controller(is_rest_controller=True)
    def raise_value_error_as_rest_controller(self, *args, **kwargs):
        raise ValueError('This is the ValueError')

    @resource_controller()
    def raise_runtime_error(self, *args, **kwargs):
        raise RuntimeError('This is the Runtime Error')

    @resource_controller(is_rest_controller=True)
    def raise_runtime_error_as_rest_controller(self, *args, **kwargs):
        raise RuntimeError('This is the Runtime Error')

    @resource_controller()
    def raise_atcore_exception(self, *args, **kwargs):
        raise ATCoreException('This is the ATCore exception.')

    @resource_controller(is_rest_controller=True)
    def raise_atcore_exception_as_rest_controller(self, *args, **kwargs):
        raise ATCoreException('This is the ATCore exception.')

    @resource_controller()
    def raise_statement_error(self, *args, **kwargs):
        raise StatementError('This is the StatementError exception', None, None, None)

    @resource_controller(is_rest_controller=True)
    def raise_statement_error_as_rest_controller(self, *args, **kwargs):
        raise StatementError('This is the StatementError exception', None, None, None)

    @resource_controller()
    def raise_no_result_found(self, *args, **kwargs):
        raise NoResultFound('This is the NoResultFound exception.')

    @resource_controller(is_rest_controller=True)
    def raise_no_result_found_as_rest_controller(self, *args, **kwargs):
        raise NoResultFound('This is the NoResultFound exception.')


class ActiveUserRequiredDecoratorTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()

        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/foo/bar/')

        # Setup mock controller
        self.mock_controller = MockController.as_controller(
            sessionmaker=sessionmaker(bind=self.connection)  # global connection (see: tethysext.atcore.tests.utilities.sqlalchemy_helpers.setup_module_for_sqlalchemy_tests)  # noqua: E501
        )

        # Setup mock resource controller
        self.mock_resource_controller = MockResourceController.as_controller(
            sessionmaker=sessionmaker(bind=self.connection)  # global connection (see: tethysext.atcore.tests.utilities.sqlalchemy_helpers.setup_module_for_sqlalchemy_tests)  # noqua: E501
        )

        messages_patcher = mock.patch('tethysext.atcore.services.app_users.decorators.messages')
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        log_patcher = mock.patch('tethysext.atcore.services.app_users.decorators.log')
        self.mock_log = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def assertIsRedirect(self, response, to='/apps/'):
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(302, response.status_code)
        self.assertEqual(to, response.url)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def test_no_request_user(self):
        self.request.user = None
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response, to='/accounts/login/?next=/foo/bar/')

    @override_settings(ENABLE_OPEN_PORTAL=False)
    def test_anonymous_user(self):
        self.request.user = AnonymousUser()
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response, to='/accounts/login/?next=/foo/bar/')

    def test_staff_user(self):
        staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )
        self.request.user = staff_user
        response = self.mock_controller(self.request)
        self.assertEqual('SUCCESS', response)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    @mock.patch('django.contrib.messages.warning')
    def test_app_user_is_none(self, _):
        self.request.user = self.user
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response)

    @override_settings(ENABLE_OPEN_PORTAL=False)
    @mock.patch('django.contrib.messages.warning')
    def test_app_user_not_active(self, _):
        app_user = AppUser(
            username=self.user.username,
            role=AppUser.ROLES.ORG_USER,
            is_active=False
        )
        self.session.add(app_user)
        self.session.commit()
        self.request.user = self.user
        response = self.mock_controller(self.request)
        self.assertIsRedirect(response)

    @mock.patch('django.contrib.messages.warning')
    def test_valid_app_user(self, _):
        app_user = AppUser(
            username=self.user.username,
            role=AppUser.ROLES.ORG_USER
        )
        self.session.add(app_user)
        self.session.commit()
        self.request.user = self.user
        response = self.mock_controller(self.request)
        self.assertEqual('SUCCESS', response)

    @override_settings(ENABLE_OPEN_PORTAL=True)
    def testactive_user_required_enable_open_portal(self):
        app_user = AppUser(
            username=self.user.username,
            role=AppUser.ROLES.ORG_USER
        )
        self.session.add(app_user)
        self.session.commit()
        self.request.user = self.user
        response = self.mock_controller(self.request)
        self.assertEqual('SUCCESS', response)

    def test_resource_controller(self):
        self.request.user = self.user
        response = self.mock_resource_controller(self.request)

        self.assertEqual('SUCCESS', response)

    def test_resource_controller_statement_error(self):
        self.request.user = self.user

        response = MockResourceController().raise_statement_error(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic resource could not be found.', msg_args[0][0][1])
        self.assertEqual('The generic resource could not be found.', self.mock_log.exception.call_args_list[0][0][0])
        self.assertEqual(MockResourceController.back_url, response.url)

    def test_resource_controller_statement_error_as_rest_controller(self):
        self.request.user = self.user

        response = MockResourceController().raise_statement_error_as_rest_controller(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic resource could not be found.', msg_args[0][0][1])
        self.assertEqual('The generic resource could not be found.', self.mock_log.exception.call_args_list[0][0][0])
        response_dict = json.loads(response._container[0])
        self.assertFalse(response_dict['success'])
        self.assertEqual('This is the StatementError exception', response_dict['error'])

    def test_resource_controller_no_result_found(self):
        self.request.user = self.user

        response = MockResourceController().raise_no_result_found(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic resource could not be found.', msg_args[0][0][1])
        self.assertEqual('The generic resource could not be found.', self.mock_log.exception.call_args_list[0][0][0])
        self.assertEqual(MockResourceController.back_url, response.url)

    def test_resource_controller_no_result_found_as_rest_controller(self):
        self.request.user = self.user

        response = MockResourceController().raise_no_result_found_as_rest_controller(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('The generic resource could not be found.', msg_args[0][0][1])
        self.assertEqual('The generic resource could not be found.', self.mock_log.exception.call_args_list[0][0][0])
        response_dict = json.loads(response._container[0])
        self.assertFalse(response_dict['success'])
        self.assertEqual('This is the NoResultFound exception.', response_dict['error'])

    def test_resource_controller_atcore_exception(self):
        self.request.user = self.user

        response = MockResourceController().raise_atcore_exception(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_args[0][0][1])
        self.assertEqual(MockResourceController.back_url, response.url)

    def test_resource_controller_atcore_exception_as_rest_controller(self):
        self.request.user = self.user

        response = MockResourceController().raise_atcore_exception_as_rest_controller(self.request)

        msg_args = self.mock_messages.warning.call_args_list
        self.assertEqual('This is the ATCore exception.', msg_args[0][0][1])
        response_dict = json.loads(response._container[0])
        self.assertFalse(response_dict['success'])
        self.assertEqual('This is the ATCore exception.', response_dict['error'])

    def test_resource_controller_value_error(self):
        self.request.user = self.user

        response = MockResourceController().raise_value_error(self.request)

        self.assertEqual(MockResourceController.back_url, response.url)

    def test_resource_controller_value_error_as_rest_controller(self):
        self.request.user = self.user

        response = MockResourceController().raise_value_error_as_rest_controller(self.request)

        response_dict = json.loads(response._container[0])
        self.assertFalse(response_dict['success'])
        self.assertEqual('This is the ValueError', response_dict['error'])

    def test_resource_controller_runtime_error(self):
        self.request.user = self.user

        response = MockResourceController().raise_runtime_error(self.request)

        msg_args = self.mock_messages.error.call_args_list
        self.assertEqual("We're sorry, an unexpected error has occurred.", msg_args[0][0][1])
        self.assertEqual('This is the Runtime Error', self.mock_log.exception.call_args_list[0][0][0])
        self.assertEqual(MockResourceController.back_url, response.url)

    def test_resource_controller_runtime_error_as_rest_controller(self):
        self.request.user = self.user

        response = MockResourceController().raise_runtime_error_as_rest_controller(self.request)

        msg_args = self.mock_messages.error.call_args_list
        self.assertEqual("We're sorry, an unexpected error has occurred.", msg_args[0][0][1])
        self.assertEqual('This is the Runtime Error', self.mock_log.exception.call_args_list[0][0][0])
        response_dict = json.loads(response._container[0])
        self.assertFalse(response_dict['success'])
        self.assertEqual('This is the Runtime Error', response_dict['error'])
