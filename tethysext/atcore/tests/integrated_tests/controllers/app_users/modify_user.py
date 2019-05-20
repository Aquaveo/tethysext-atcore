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
from sqlalchemy.orm.exc import NoResultFound
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.controllers.app_users.modify_user import ModifyUser
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ModifyUserTests(SqlAlchemyTestCase):

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

        self.mock_members = mock.MagicMock()
        self.mock_client = mock.MagicMock()
        self.mock_resource = mock.MagicMock(DISPLAY_TYPE_PLURAL=[])

        self.organization = Organization(
            name='Test_org',
            active=True,
            license='advanced',
        )

        self.organization.members.append(self.app_user)
        self.session.add(self.app_user)
        self.session.commit()

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.ModifyUser._handle_modify_user_requests')
    def test_get(self, mock_handle_modify_user):
        mock_request = mock.MagicMock()
        modify_user = ModifyUser()
        modify_user.get(mock_request)

        # test the results
        mock_handle_modify_user.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.ModifyUser._handle_modify_user_requests')
    def test_post(self, mock_handle_modify_user):
        mock_request = mock.MagicMock()

        modify_user = ModifyUser()
        modify_user.post(mock_request)

        # test the results
        mock_handle_modify_user.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post(self, _, mock_get_app_user_model, mock_get_organization_model,
                                               mock_get_sessionmaker, mock_get_active_app,
                                               mock_get_permissions_manager, __, mock_reverse):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'first-name': 'Foo', 'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc123', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1', 'Org2']}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['Role1', 'Role2']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=mock_request.user.id)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        session.commit.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        mock_get_permissions_manager.assert_called()

        self.assertEqual('NameSpace:app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post_create_new_client(self, _, mock_get_app_user_model,
                                                                 mock_get_organization_model, mock_get_sessionmaker,
                                                                 mock_get_active_app, mock_get_permissions_manager, __,
                                                                 mock_reverse):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'username': 'user1', 'first-name': 'Foo',
                     'last-name': 'Bar', 'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc123', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1', 'Org2']}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['Role1', 'Role2']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        session.commit.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        mock_get_permissions_manager.assert_called()

        self.assertEqual('NameSpace:app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_user_not_found_exception(self, _, mock_get_app_user_model,
                                                                   __, mock_get_sessionmaker, mock_get_active_app, ___,
                                                                   mock_reverse, mock_messages):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'username': 'user1', 'first-name': 'Foo',
                     'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc123', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1', 'Org2']}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()

        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['Role1', 'Role2']

        mock_get_active_app().namespace = 'NameSpace'

        mock_edit_session = mock_get_sessionmaker()()
        mock_edit_session.query().filter().one.side_effect = NoResultFound

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=mock_request.user.id)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        mock_messages.warning.assert_called_with(mock_request, 'The user could not be found.')
        mock_edit_session.close.assert_called()

        self.assertEqual('NameSpace:app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post_create_new_invalid_client(self, _, mock_get_app_user_model,
                                                                         __, mock_get_sessionmaker, mock_get_active_app,
                                                                         mock_render):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'first-name': 'Foo',
                     'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc1234', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1', 'Org2']}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()

        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['APP_ADMIN']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()

        session.close.assert_called()

        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations

        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['username_input']['initial'])
        self.assertEqual('Username is required.', mock_render.call_args_list[0][0][2]['username_input']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['password_input']['error'])

        self.assertEqual('abc1234', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertEqual('Passwords do not match.',
                         mock_render.call_args_list[0][0][2]['confirm_password_input']['error'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])

        self.assertEqual('DEVELOPER', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertListEqual(['Org1', 'Org2'], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_get(self, _, mock_get_app_user_model, mock_get_organization_model,
                                              mock_get_sessionmaker, mock_get_active_app, mock_render):
        mock_dict = {'next': 'manage-organizations'}
        mock_request = self.request_factory.get('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()
        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['APP_ADMIN', 'DEVELOPER']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)

        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertEqual('NameSpace:app_users_manage_organizations',
                         mock_render.call_args_list[0][0][2]['next_controller'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['is_me'])
        self.assertListEqual(['APP_ADMIN', 'DEVELOPER'], mock_render.call_args_list[0][0][2]['no_organization_roles'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post_create_new_client_is_me(self, _, mock_get_app_user_model,
                                                                       __,
                                                                       mock_get_sessionmaker,
                                                                       mock_get_active_app,
                                                                       mock_render):

        mock_dict = {'modify-user-submit': 'modify-user-submit', 'username': 'user1 sam', 'first-name': 'Foo',
                     'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc123', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1']}
        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()
        mock_request_app_user = mock.MagicMock()
        mock_request_app_user.id = mock_request.user.id

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['DEVELOPER']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=str(mock_request.user.id))

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])

        self.assertEqual('DEVELOPER', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertListEqual([], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('You cannot remove yourself from all organization. You must belong to at least one.',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post_password_confirm_password_user_space_error(self, _,
                                                                                          mock_get_app_user_model,
                                                                                          __, mock_get_sessionmaker,
                                                                                          mock_get_active_app,
                                                                                          mock_render):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'first-name': 'Foo',
                     'last-name': 'Bar', 'username': 'foo bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': '',
                     'password-confirm': '', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1', 'Org2']}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()

        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['APP_ADMIN']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()

        session.close.assert_called()

        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertEqual('foo bar', mock_render.call_args_list[0][0][2]['username_input']['initial'])
        self.assertEqual('Username cannot contain a space.',
                         mock_render.call_args_list[0][0][2]['username_input']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertEqual('Password is required.', mock_render.call_args_list[0][0][2]['password_input']['error'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertEqual('Please confirm password.',
                         mock_render.call_args_list[0][0][2]['confirm_password_input']['error'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])

        self.assertEqual('DEVELOPER', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertListEqual(['Org1', 'Org2'], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_post_duplicate_username(self, _, mock_get_app_user_model,
                                                                  __, mock_get_sessionmaker, mock_get_active_app,
                                                                  mock_render):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'first-name': 'Foo',
                     'last-name': 'Bar', 'username': self.app_user.username,
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': '',
                     'password-confirm': '', 'assign-role': [Roles.ORG_ADMIN]}

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()

        session = mock_get_sessionmaker()()

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        # app_user.ROLES.get_no_organization_roles.return_value = [Roles.ORG_ADMIN]
        app_user.ROLES.get_organization_required_roles.return_value = [Roles.ORG_ADMIN]

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()

        session.close.assert_called()

        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertEqual(self.app_user.username, mock_render.call_args_list[0][0][2]['username_input']['initial'])
        self.assertEqual('The given username already exists. Please, choose another.',
                         mock_render.call_args_list[0][0][2]['username_input']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertEqual('Password is required.', mock_render.call_args_list[0][0][2]['password_input']['error'])

        self.assertEqual('', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertEqual('Please confirm password.',
                         mock_render.call_args_list[0][0][2]['confirm_password_input']['error'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])

        self.assertEqual(str(Roles.ORG_ADMIN), mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('Must assign user to at least one organization',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_validate_edit_confirm_password(self, _, mock_get_app_user_model,
                                                                         __, mock_get_sessionmaker,
                                                                         mock_get_active_app, mock_render):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'username': 'user1 sam', 'first-name': 'Foo',
                     'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': '', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1']}
        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()
        mock_request_app_user = mock.MagicMock()
        mock_request_app_user.id = mock_request.user.id

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['DEVELOPER']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=str(mock_request.user.id))

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertEqual('Please confirm password.',
                         mock_render.call_args_list[0][0][2]['confirm_password_input']['error'])

        self.assertEqual('DEVELOPER', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertListEqual([], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('You cannot remove yourself from all organization. You must belong to at least one.',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_user_requests_validate_edit__password_confirm_password(self, _, mock_get_app_user_model,
                                                                                   __, mock_get_sessionmaker,
                                                                                   mock_get_active_app, mock_render):
        mock_dict = {'modify-user-submit': 'modify-user-submit', 'username': 'user1 sam', 'first-name': 'Foo',
                     'last-name': 'Bar',
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc1234', 'assign-role': ['APP_ADMIN', 'DEVELOPER'],
                     'assign-organizations': ['Org1']}
        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        session = mock_get_sessionmaker()()
        mock_request_app_user = mock.MagicMock()
        mock_request_app_user.id = mock_request.user.id

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_no_organization_roles.return_value = ['DEVELOPER']

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=str(mock_request.user.id))

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True, cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['password_input']['initial'])
        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])
        self.assertEqual('abc1234', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])
        self.assertEqual('Passwords do not match.',
                         mock_render.call_args_list[0][0][2]['confirm_password_input']['error'])

        self.assertEqual('DEVELOPER', mock_render.call_args_list[0][0][2]['role_select']['initial'])
        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])
        self.assertEqual('', mock_render.call_args_list[0][0][2]['role_select']['error'])
        self.assertFalse(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])
        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
        self.assertListEqual([], mock_render.call_args_list[0][0][2]['organization_select']['initial'])
        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])
        self.assertEqual('You cannot remove yourself from all organization. You must belong to at least one.',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.render')
    @mock.patch('tethysext.atcore.controllers.app_users.modify_user.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test__handle_modify_normal_user_change_role(self, _, mock_get_app_user_model, __, mock_get_sessionmaker,
                                                    mock_get_active_app, mock_render):

        mock_dict = {'modify-user-submit': 'modify-user-submit', 'first-name': 'Foo',
                     'last-name': 'Bar', 'username': self.app_user.username,
                     'user-account-status': 'on', 'email': 'user@aquaveo.com', 'password': 'abc123',
                     'password-confirm': 'abc123', 'assign-role': [Roles.ORG_ADMIN]}

        self.django_user.is_staff = False

        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)

        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()

        session = mock_get_sessionmaker()()

        mock_target_user = mock.MagicMock()

        mock_target_user.username = self.app_user.username

        session.query().filter().one.return_value = mock_target_user

        mock_target_user.get_organizations.return_value = [self.organization]

        mock_request_app_user = mock.MagicMock()

        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_request_app_user.get_organizations.return_value = self.organization

        mock_request_app_user.get_assignable_roles.return_value = [Roles.ORG_ADMIN]

        app_user.ROLES.get_organization_required_roles.return_value = [Roles.ORG_ADMIN]

        mock_get_active_app().namespace = 'NameSpace'

        # call method
        modify_user = ModifyUser()
        modify_user._handle_modify_user_requests(mock_request, user_id=self.app_user.id)

        # test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        mock_request_app_user.get_organizations.assert_called_with(session, mock_request, as_options=True,
                                                                   cascade=True)
        mock_request_app_user.get_assignable_roles.assert_called_with(mock_request, as_options=True)
        app_user.ROLES.get_no_organization_roles.assert_called()

        session.close.assert_called()

        mock_get_active_app.assert_called_with(mock_request)

        # testing form validations
        self.assertEqual('Foo', mock_render.call_args_list[0][0][2]['first_name_input']['initial'])

        self.assertEqual('Bar', mock_render.call_args_list[0][0][2]['last_name_input']['initial'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['username_input']['disabled'])

        self.assertEqual(mock_target_user.get_django_user().username,
                         mock_render.call_args_list[0][0][2]['username_input']['initial'])

        self.assertEqual('user@aquaveo.com', mock_render.call_args_list[0][0][2]['email_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['password_input']['initial'])

        self.assertEqual('abc123', mock_render.call_args_list[0][0][2]['confirm_password_input']['initial'])

        self.assertTrue(mock_render.call_args_list[0][0][2]['user_account_status_toggle']['initial'])

        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['initial'])

        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['initial'])

        self.assertEqual('user_role_org_admin', mock_render.call_args_list[0][0][2]['role_select']['options'][0])

        self.assertTrue(mock_render.call_args_list[0][0][2]['role_select']['disabled'])

        self.assertEqual(self.organization, mock_render.call_args_list[0][0][2]['organization_select']['options'])

        self.assertEqual('Must assign user to at least one organization',
                         mock_render.call_args_list[0][0][2]['organization_select']['error'])

        self.assertEqual(mock_request, mock_render.call_args_list[0][0][0])

        self.assertEqual('atcore/app_users/modify_user.html', mock_render.call_args_list[0][0][1])
