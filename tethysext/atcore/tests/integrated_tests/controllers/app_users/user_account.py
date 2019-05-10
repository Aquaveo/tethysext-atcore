"""
********************************************************************************
* Name: user_account.py
* Author: nswain, Teva
* Created On: December 11, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from django.test import RequestFactory
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.user_account import UserAccount
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class UserAccountTest(SqlAlchemyTestCase):

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

        self.resource = Resource(
            name="resource1",
            description="a resource",
            status="available",
        )

        self.organization = Organization(
            name="organization1",
            license=Organization.LICENSES.STANDARD
        )

        self.organization.resources.extend([self.resource])
        self.session.add(self.resource)
        self.session.add(self.organization)
        self.session.commit()

    @mock.patch('tethysext.atcore.controllers.app_users.user_account.UserAccount._handle_get')
    def test_get(self, mock_handle):
        user_account = UserAccount()
        mock_request = mock.MagicMock()

        # call the method
        user_account.get(mock_request)

        # test results
        mock_handle.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.user_account.render')
    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    def test_handle_get(self, mock_app_user_model, mock_get_org, mock_get_session, mock_get_permission, _, mock_render):
        session = mock_get_session()()

        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_request.user = self.django_user

        request_app_user = mock.MagicMock()
        mock_app_user_model().get_app_user_from_request.return_value = request_app_user

        request_app_user.get_organizations.return_value = [self.organization]

        mock_permission_group = mock.MagicMock()

        mock_get_permission.get_all_permissions_groups_for.return_value = mock_permission_group

        # call the method
        user_account = UserAccount()
        user_account._handle_get(mock_request)

        # test results
        mock_get_app_user_call_args = mock_app_user_model().get_app_user_from_request.call_args_list
        self.assertEqual(mock_request, mock_get_app_user_call_args[0][0][0])
        self.assertEqual(session, mock_get_app_user_call_args[0][0][1])

        mock_get_org_call_args = request_app_user.get_organizations.call_args_list
        self.assertEqual(session, mock_get_org_call_args[0][0][0])
        self.assertEqual(mock_request, mock_get_org_call_args[0][0][1])
        self.assertFalse(mock_get_org_call_args[0][1]['cascade'])

        mock_permission_manager_call_args = mock_get_permission().get_all_permissions_groups_for.call_args_list
        self.assertEqual(request_app_user, mock_permission_manager_call_args[0][0][0])

        mock_render_call_args = mock_render.call_args_list
        self.assertEqual(mock_request, mock_render_call_args[0][0][0])
        self.assertEqual('atcore/app_users/user_account.html', mock_render_call_args[0][0][1])
        self.assertEqual('organization1', mock_render_call_args[0][0][2]['organizations'][0]['name'])
        self.assertEqual('atcore/app_users/base.html', mock_render_call_args[0][0][2]['base_template'])
        self.assertEqual('Active', mock_render_call_args[0][0][2]['user_account_status'])
        self.assertEqual('My Account', mock_render_call_args[0][0][2]['page_title'])

        session.close.assert_called()

    # TODO: Line 53 needs to be covered in the following
    # @mock.patch('tethysext.atcore.controllers.app_users.user_account.render')
    # @mock.patch('tethys_apps.utilities.get_active_app')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    # @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    # def test_handle_get_not_request_user(self, mock_app_user_model, mock_get_org, mock_get_session,
    # mock_get_permission, _, mock_render):
    #     session = mock_get_session()()
    #
    #     mock_request = self.request_factory.get('/foo/bar/map-view/')
    #     mock_request.user = self.django_user
    #
    #     request_app_user = mock.MagicMock()
    #     mock_app_user_model().get_app_user_from_request.return_value = None
    #
    #     request_app_user.get_organizations.return_value = [self.organization]
    #
    #     mock_permission_group = mock.MagicMock()
    #
    #     mock_get_permission.get_all_permissions_groups_for.return_value = mock_permission_group
    #
    #     # call the method
    #     user_account = UserAccount()
    #     user_account._handle_get(mock_request)
    #
    #     # test results
    #     mock_get_app_user_call_args = mock_app_user_model().get_app_user_from_request.call_args_list
    #     self.assertEqual(mock_request, mock_get_app_user_call_args[0][0][0])
    #     self.assertEqual(session, mock_get_app_user_call_args[0][0][1])
    #
    #     mock_get_org_call_args = request_app_user.get_organizations.call_args_list
    #     self.assertEqual(session, mock_get_org_call_args[0][0][0])
    #     self.assertEqual(mock_request, mock_get_org_call_args[0][0][1])
    #     self.assertFalse(mock_get_org_call_args[0][1]['cascade'])
    #
    #     mock_permission_manager_call_args = mock_get_permission().get_all_permissions_groups_for.call_args_list
    #     self.assertEqual(request_app_user, mock_permission_manager_call_args[0][0][0])
    #
    #     mock_render_call_args = mock_render.call_args_list
    #     self.assertEqual(mock_request, mock_render_call_args[0][0][0])
    #     self.assertEqual('atcore/app_users/user_account.html', mock_render_call_args[0][0][1])
    #     self.assertEqual('organization1', mock_render_call_args[0][0][2]['organizations'][0]['name'])
    #     self.assertEqual('atcore/app_users/base.html', mock_render_call_args[0][0][2]['base_template'])
    #     self.assertEqual('Active', mock_render_call_args[0][0][2]['user_account_status'])
    #     self.assertEqual('My Account', mock_render_call_args[0][0][2]['page_title'])
    #
    #     session.close.assert_called()
