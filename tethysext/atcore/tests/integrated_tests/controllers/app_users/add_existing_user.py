"""
********************************************************************************
* Name: modify_user.py
* Author: Teva, Tanner
* Created On: December 21, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
from django.test import RequestFactory
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.add_existing_user import AddExistingUser
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class AddExistingUserTests(SqlAlchemyTestCase):

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

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.AddExistingUser._handle_modify_user_requests')
    def test_get(self, mock_handle_modify_user):
        mock_request = mock.MagicMock()
        add_existing_user = AddExistingUser()
        add_existing_user.get(mock_request)

        # test the results
        mock_handle_modify_user.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.AddExistingUser._handle_modify_user_requests')
    def test_post(self, mock_handle_modify_user):
        mock_request = mock.MagicMock()

        add_existing_user = AddExistingUser()
        add_existing_user.post(mock_request)

        # test the results
        mock_handle_modify_user.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    def test__handle_modify_user_requests(self, mock_get_app_usermodel, _,
                                          mock_get_session_maker, mock_get_active_app,
                                          mock_get_permission_manager, __, mock_reverse):
        session = mock_get_session_maker()()

        mock_dict = {'add-existing-user-submit': 'add-existing-user-submit', 'assign-role': 'Role1',
                     'portal-users': 'portal_user1', 'assign-organizations': 'org1'}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        mock_request_app_user = mock.MagicMock()
        mock_get_app_usermodel().get_app_user_from_request.return_value = mock_request_app_user

        mock_org = mock.MagicMock()
        mock_request_app_user.get_organizations.return_value = mock_org

        mock_role = mock.MagicMock()
        mock_request_app_user.get_assignable_roles.return_value = mock_role

        mock_no_of_orgs = mock.MagicMock()
        mock_get_app_usermodel().ROLES.get_no_organization_roles.return_value = mock_no_of_orgs

        mock_get_active_app().namespace = 'NameSpace'

        # call the method
        add_existing_user = AddExistingUser()
        add_existing_user._handle_modify_user_requests(mock_request)

        # testing the results
        session.close.assert_called()
        mock_get_app_usermodel().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request,  as_options=True)

        mock_get_active_app.assert_called_with(mock_request)

        mock_get_permission_manager.assert_called()

        mock_get_permission_manager().remove_all_permissions_groups.assert_called()

        self.assertEqual('NameSpace:app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    def test__handle_modify_user_requests_permission_manager(self, mock_get_app_usermodel, mock_get_organization_model,
                                                             mock_get_session_maker, mock_get_active_app,
                                                             mock_get_permission_manager, _, mock_reverse):
        session = mock_get_session_maker()()

        mock_dict = {'add-existing-user-submit': 'add-existing-user-submit', 'assign-role': 'Role1',
                     'portal-users': 'portal_user1', 'assign-organizations': 'org1'}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        mock_request_app_user = mock.MagicMock()
        mock_get_app_usermodel().get_app_user_from_request.return_value = mock_request_app_user

        mock_org = mock.MagicMock()
        mock_request_app_user.get_organizations.return_value = mock_org

        mock_role_option = mock.MagicMock()
        mock_request_app_user.get_assignable_roles.return_value = mock_role_option

        mock_get_app_usermodel().ROLES.get_no_organization_roles.return_value = ['Role1']

        mock_get_active_app().namespace = 'NameSpace'

        # call the method
        add_existing_user = AddExistingUser()
        add_existing_user._handle_modify_user_requests(mock_request)

        # testing the results
        session.close.assert_called()
        mock_get_app_usermodel().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)

        mock_get_active_app.assert_called_with(mock_request)

        mock_get_permission_manager.assert_called()

        self.assertEqual('Role1', mock_get_permission_manager().assign_user_permission.call_args[0][1])

        self.assertEqual('NameSpace:app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    def test__handle_modify_user_requests_must_assign_user(self, mock_get_app_usermodel, _,
                                                           mock_get_session_maker, mock_get_active_app,
                                                           __, mock_render):
        session = mock_get_session_maker()()

        mock_dict = {'add-existing-user-submit': 'add-existing-user-submit', 'assign-role': 'role1',
                     'portal-users': 'portal_user1'}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        mock_request_app_user = mock.MagicMock()
        mock_get_app_usermodel().get_app_user_from_request.return_value = mock_request_app_user

        mock_org_option = mock.MagicMock()
        mock_request_app_user.get_organizations.return_value = mock_org_option

        mock_role_option = mock.MagicMock()
        mock_request_app_user.get_assignable_roles.return_value = mock_role_option

        mock_no_of_orgs = mock.MagicMock()
        mock_get_app_usermodel().ROLES.get_no_organization_roles.return_value = mock_no_of_orgs

        mock_get_active_app().namespace = 'NameSpace'

        mock_get_app_usermodel().ROLES.get_organization_required_roles.return_value = ['role1']

        # call the method
        add_existing_user = AddExistingUser()
        add_existing_user._handle_modify_user_requests(mock_request)

        # testing the results
        session.close.assert_called()
        mock_get_app_usermodel().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)

        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/add_existing_user.html', mock_render.call_args_list[0][0][1])

        self.assertEqual('portal_user1',
                         mock_render.call_args_list[0][0][2]['portal_users_select']['initial'][0])

        self.assertEqual('role1', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual(mock_role_option, mock_render.call_args_list[0][0][2]['role_select']['options'])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['error'])

        self.assertEqual([], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(mock_org_option, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('Must assign user to at least one organization',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.add_existing_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    def test__handle_modify_user_requests_with_invalid_post_data(self, mock_get_app_usermodel, _,
                                                                 mock_get_session_maker, mock_get_active_app,
                                                                 mock_render):
        session = mock_get_session_maker()()

        mock_dict = {'add-existing-user-submit': 'add-existing-user-submit', 'assign-role': '',
                     'portal-users': [], 'assign-organizations': []}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        mock_request_app_user = mock.MagicMock()
        mock_get_app_usermodel().get_app_user_from_request.return_value = mock_request_app_user

        mock_org = mock.MagicMock()
        mock_request_app_user.get_organizations.return_value = mock_org

        mock_role = mock.MagicMock()
        mock_request_app_user.get_assignable_roles.return_value = mock_role

        mock_no_of_orgs = mock.MagicMock()
        mock_get_app_usermodel().ROLES.get_no_organization_roles.return_value = [mock_no_of_orgs]

        mock_get_active_app().namespace = 'NameSpace'

        # call the method
        add_existing_user = AddExistingUser()
        add_existing_user._handle_modify_user_requests(mock_request)

        # testing the results
        mock_get_app_usermodel().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)

        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/add_existing_user.html', mock_render.call_args_list[0][0][1])

        self.assertEqual('Must select at least one user.',
                         mock_render.call_args_list[0][0][2]['portal_users_select']['error'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual(mock_role, mock_render.call_args_list[0][0][2]['role_select']['options'])
        self.assertEqual('A role must be assigned to user.',
                         mock_render.call_args_list[0][0][2]['role_select']['error'])

        self.assertEqual([], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(mock_org, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['organization_select']['error'])
