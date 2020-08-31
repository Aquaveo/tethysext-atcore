"""
********************************************************************************
* Name: manage_organizations.py
* Author: Tanner and Teva
* Created On: September 24, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
from django.test import RequestFactory
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.controllers.app_users.manage_organizations import ManageOrganizations
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ManageOrganizationsTests(SqlAlchemyTestCase):

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
        self.session.commit()
        self.request_factory = RequestFactory()

        self.mock_members = mock.MagicMock()
        self.mock_client = mock.MagicMock()
        self.mock_resource = mock.MagicMock(DISPLAY_TYPE_PLURAL=[])

        self.organization = Organization(
            name='Test_org',
            active=True,
            license='advanced',
            members=[self.mock_members],
            clients=[self.mock_client],
            resources=self.mock_resource,
            consultant=mock.MagicMock()
        )

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.ManageOrganizations._handle_get')
    def test_get(self, mock_handle):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        # call the method
        manage_organizations = ManageOrganizations()
        manage_organizations.get(mock_request)

        # test the results
        mock_handle.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.ManageOrganizations._handle_delete')
    def test_delete(self, mock_delete):
        mock_request = mock.MagicMock()
        mock_request.GET.get.side_effect = ['delete', '001']

        # call the method
        manage_organizations = ManageOrganizations()
        manage_organizations.delete(mock_request)

        # test the results
        mock_delete.assert_called_with(mock_request, '001')

    def test_not_delete(self):
        mock_request = mock.MagicMock()
        mock_request.GET.get.side_effect = ['foo', '001']

        # call the method
        manage_organizations = ManageOrganizations()
        ret = manage_organizations.delete(mock_request)

        # test the results
        self.assertIn('"success": false', ret.content.decode("utf-8"))
        self.assertIn('"error": "Invalid action: foo"', ret.content.decode("utf-8"))

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.render')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.ManageOrganizations.add_custom_fields')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_get(self, _, mock_get_app_user, mock_get_session, __, mock_has_permissions,
                        ___, mock_render):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        mock_app_user = mock.MagicMock()
        mock_make_session = mock_get_session()()

        mock_get_app_user().get_app_user_from_request.return_value = mock_app_user

        mock_make_session.query().all.return_value = [self.organization]

        mock_app_user.is_staff.return_value = True
        mock_has_permissions.return_value = True

        # call the method
        manage_organizations = ManageOrganizations()
        manage_organizations._handle_get(mock_request)

        # Test
        mock_make_session.close.assert_called()
        self.assertTrue(mock_request == mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/manage_organizations.html', mock_render.call_args_list[0][0][1])
        self.assertTrue(mock_render.call_args_list[0][0][2]['show_resources_link'])
        self.assertEqual('atcore/app_users/base.html', mock_render.call_args_list[0][0][2]['base_template'])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.render')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.ManageOrganizations.add_custom_fields')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethys_apps.utilities.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_get_not_staff(self, _, mock_get_app_user, mock_get_session, ___, mock_has_permissions, ____,
                                  mock_render):
        mock_request = self.request_factory.get('/foo/bar/')
        mock_request.user = self.django_user

        mock_app_user = mock.MagicMock()

        mock_get_app_user().get_app_user_from_request.return_value = mock_app_user

        mock_make_session = mock_get_session()()

        mock_app_user.is_staff.return_value = False
        mock_has_permissions.side_effect = [False, True, True, True, True, True, True, True, True]

        self.organization.resources = [mock.MagicMock(DISPLAY_TYPE_PLURAL='RESOURCES')]
        mock_app_user.get_organizations.return_value = [self.organization]

        # call the method
        manage_organizations = ManageOrganizations()
        manage_organizations._handle_get(mock_request)

        # Test
        mock_make_session.close.assert_called()

        self.assertTrue(mock_request == mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/manage_organizations.html', mock_render.call_args_list[0][0][1])
        self.assertTrue(mock_render.call_args_list[0][0][2]['show_resources_link'])
        self.assertEqual('atcore/app_users/base.html', mock_render.call_args_list[0][0][2]['base_template'])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.'
                'ManageOrganizations.perform_custom_delete_operations')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_delete(self, _, mock_get_app_user, mock_session, mock_perform_delete, mock_has_permission):
        mock_request = mock.MagicMock()
        mock_make_session = mock_session()()
        mock_app_user = mock.MagicMock()

        mock_get_app_user().get_app_user_from_request.return_value = mock_app_user

        mock_make_session.query().get.return_value = self.organization

        # call the method
        organization_id = 'O001'
        manage_organizations = ManageOrganizations()
        ret = manage_organizations._handle_delete(mock_request, organization_id)

        # test the results
        mock_perform_delete.assert_called_with(mock_request, self.organization)
        mock_has_permission.assert_called_with(mock_request, 'delete_organizations')
        mock_make_session.delete.assert_called_with(self.organization)
        mock_make_session.commit.assert_called()
        mock_make_session.close.assert_called()
        self.assertEqual(200, ret.status_code)
        self.assertEqual('{"success": true}', ret.content.decode('utf-8'))

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.'
                'ManageOrganizations.perform_custom_delete_operations')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_delete_can_delete_organization(self, _, mock_get_app_user, mock_session,
                                                   mock_perform_delete, mock_has_permission):
        mock_request = mock.MagicMock()
        mock_make_session = mock_session()()

        consultant = mock.MagicMock()

        role = mock.MagicMock(ORG_ADMIN=Roles.ORG_ADMIN)
        app_user = mock.MagicMock(ROLES=role)
        mock_get_app_user.return_value = app_user

        mock_app_user = mock.MagicMock(organizations=[consultant], role=Roles.ORG_ADMIN)
        app_user.get_app_user_from_request.return_value = mock_app_user

        self.organization.consultant = consultant
        mock_make_session.query().get.return_value = self.organization

        # call the method
        organization_id = 'O001'
        manage_organizations = ManageOrganizations()
        ret = manage_organizations._handle_delete(mock_request, organization_id)

        # test the results
        mock_perform_delete.assert_called_with(mock_request, self.organization)
        mock_has_permission.assert_called_with(mock_request, 'delete_organizations')
        mock_make_session.delete.assert_called_with(self.organization)
        mock_make_session.commit.assert_called()
        mock_make_session.close.assert_called()
        self.assertEqual(200, ret.status_code)
        self.assertEqual('{"success": true}', ret.content.decode('utf-8'))

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.HttpResponseForbidden')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.'
                'ManageOrganizations.perform_custom_delete_operations')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_delete_http_response_forbidden(self, _, mock_get_app_user, mock_session, mock_perform_delete,
                                                   mock_has_permission, mock_hrf):
        mock_request = mock.MagicMock()
        mock_make_session = mock_session()()
        mock_app_user = mock.MagicMock()

        mock_get_app_user().get_app_user_from_request.return_value = mock_app_user

        mock_make_session.query().get.return_value = self.organization

        mock_has_permission.return_value = False

        # call the method
        organization_id = 'O001'
        manage_organizations = ManageOrganizations()

        manage_organizations._handle_delete(mock_request, organization_id)

        # test the results
        mock_perform_delete.assert_called_with(mock_request, self.organization)
        mock_has_permission.assert_called_with(mock_request, 'delete_organizations')
        mock_hrf.assert_called()

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.has_permission')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organizations.'
                'ManageOrganizations.perform_custom_delete_operations')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    def test_handle_delete_exception(self, _, mock_get_app_user, mock_session, __, ___):
        mock_request = mock.MagicMock()
        mock_make_session = mock_session()()

        mock_get_app_user().get_app_user_from_request.side_effect = Exception

        # call the method
        organization_id = 'O001'
        manage_organizations = ManageOrganizations()

        ret = manage_organizations._handle_delete(mock_request, organization_id)

        # test the results
        mock_make_session.close.assert_called()
        mock_make_session.commit.assert_not_called()
        mock_make_session.delete.assert_not_called()
        self.assertIn('"success": false', ret.content.decode("utf-8"))
        self.assertIn('"error": "Exception()"', ret.content.decode("utf-8"))

    def test_add_custom_fields(self):
        test_card = {'foo': 1, 'bar': 2, 'baz': 3}

        # call the method
        manage_organizations = ManageOrganizations()
        ret = manage_organizations.add_custom_fields(mock.MagicMock(), test_card)

        # test the results
        self.assertDictEqual(test_card, ret)

    def test_preform_custom_delete_operations(self):
        ManageOrganizations().perform_custom_delete_operations(None, None)
