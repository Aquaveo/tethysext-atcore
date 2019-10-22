"""
********************************************************************************
* Name: resource_details_tests.py
* Author: mlebaron
* Created On: October 2, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from django.contrib.auth.models import User
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

        staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.user = staff_user

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

        back = ResourceDetails().default_back_url(self.request)

        self.assertEqual('app_namespace:app_users_manage_organizations', back._mock_new_parent.call_args[0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.resource_details.get_active_app')
    def test_default_back_url_without_back(self, mock_get_active_app, mock_reverse):
        namespace = 'app_namespace'
        mock_get_active_app.return_value = mock.MagicMock(namespace=namespace)
        self.request.GET = {}

        back = ResourceDetails().default_back_url(self.request)

        self.assertEqual('app_namespace:app_users_manage_resources', back._mock_new_parent.call_args[0][0])

    def test_get_context(self):
        context = {'success': True}

        ret = ResourceDetails().get_context(self.request, context)

        self.assertTrue(ret['success'])
