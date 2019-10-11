"""
********************************************************************************
* Name: modify_organization_tests.py
* Author: mlebaron
* Created On: October 10, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.controllers.app_users.modify_organization import ModifyOrganization
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ModifyOrganizationsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        app_user = AppUser(
            username=self.user.username,
            role=AppUser.ROLES.ORG_USER,
            is_active=False
        )
        self.session.add(app_user)
        self.session.commit()
        self.request = mock.MagicMock()
        self.request.user = self.user

    def tearDown(self):
        super().tearDown()

    @mock.patch('tethysext.atcore.controllers.app_users.modify_organization.ModifyOrganization._handle_modify_user_requests')
    def test_get(self, mock_handle):
        self.request.method = 'get'
        controller = ModifyOrganization.as_controller()

        ret = controller(self.request)

        mock_handle.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.modify_organization.ModifyOrganization._handle_modify_user_requests')
    def test_post(self, mock_handle):
        self.request.method = 'post'
        controller = ModifyOrganization.as_controller()

        ret = controller(self.request)

        mock_handle.assert_called()

    @mock.patch('tethysext.atcore.models.app_users.organization.Organization.can_add_client_with_license')
    @mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.must_have_consultant')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    def test_get_license_to_consultant_map(self, mock_get_sessionmaker, mock_must_have_consultant,
                                           mock_can_add_client_with_license):
        mock_get_sessionmaker.return_value = mock.MagicMock()
        mock_must_have_consultant.return_value = True
        mock_can_add_client_with_license.return_value = True
        license_options = [('Standard', 'standard')]
        org = mock.MagicMock(spec=Organization, id=123456)
        organizations = [org]

        licenses = ModifyOrganization().get_license_to_consultant_map(self.request, license_options, organizations)

        self.assertEqual(['123456'], licenses['standard'])

    @mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.list')
    def test_get_hide_consultant_licenses(self, mock_list):
        mock_list.return_value = ('standard', 'advanced', 'garbage', 'professional', 'enterprise')
        modify_organization = ModifyOrganization()

        licenses = modify_organization.get_hide_consultant_licenses(self.request)

        self.assertEqual(['garbage', 'enterprise'], licenses)

    def test_handle_modify_user_requests(self):
        ModifyOrganization()._handle_modify_user_requests(self.request)
