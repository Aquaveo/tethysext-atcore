"""
********************************************************************************
* Name: user_account.py
* Author: nswain, Teva
* Created On: December 11, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
from django.test import RequestFactory
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.controllers.app_users.manage_organization_members import ManageOrganizationMembers
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ManageOrganizationMembersTest(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()
        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()

        self.django_user2 = UserFactory()
        self.django_user2.is_staff = True
        self.django_user2.is_superuser = True
        self.django_user2.save()

        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.user_org_member = AppUser(
            username=self.django_user2.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.org_user_consultant = AppUser(
            username='org_consultant',
            role=Roles.ORG_ADMIN,
            is_active=True,
        )

        self.resource = Resource(
            name="resource1",
            description="a resource",
            status="available",
        )

        self.organization = Organization(
            name='test_organization',
            active=True,
            license='advanced'
        )

        self.child_organization = Organization(
            name='child_organization',
            active=True,
            license='advanced'
        )

        self.organization.members.append(self.user_org_member)
        self.organization.clients.append(self.child_organization)
        self.organization.resources.append(self.resource)

        self.session.add(self.org_user_consultant)
        self.session.add(self.user_org_member)
        self.session.add(self.app_user)
        self.session.commit()

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.'
                'ManageOrganizationMembers._handle_manage_member_request')
    def test_get(self, mock_handle_manage_memeber_request):
        manage_organization_members = ManageOrganizationMembers()
        mock_request = mock.MagicMock()

        # call the method
        manage_organization_members.get(mock_request)

        # test results
        mock_handle_manage_memeber_request.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.'
                'ManageOrganizationMembers._handle_manage_member_request')
    def test_post(self, mock_handle_manage_memeber_request):
        manage_organization_members = ManageOrganizationMembers()
        mock_request = mock.MagicMock()

        # call the method
        manage_organization_members.post(mock_request)

        # test results
        mock_handle_manage_memeber_request.assert_called_with(mock_request)

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.render')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_handle_manage_member_request_get(self, _, mock_get_user_model, __,
                                              mock_get_sessionmaker, ___, mock_render):
        app_user = mock_get_user_model()
        make_session = mock_get_sessionmaker()

        mock_dict = {'next': 'manage-organizations'}
        mock_request = self.request_factory.get('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        session = make_session()

        session.query().get.return_value = self.organization
        mock_request_app_user = mock.MagicMock()
        app_user.get_app_user_from_request.return_value = mock_request_app_user

        mock_peer_user = mock.MagicMock()
        mock_peer_user.id = 1
        mock_peer_user.user_name = 'user1'
        mock_peer_user.get_display_name.return_value = 'User1'
        mock_request_app_user.get_peers.return_value = [mock_peer_user]

        # call the method
        manage_organization_members = ManageOrganizationMembers()
        manage_organization_members._handle_manage_member_request(mock_request, 'O001')

        # Test the results
        app_user.get_app_user_from_request.assert_called_with(mock_request, session)

        call_args = mock_render.call_args_list
        self.assertEqual(mock_request, call_args[0][0][0])
        self.assertEqual('atcore/app_users/manage_organization_members.html', call_args[0][0][1])
        self.assertEqual('test_organization', call_args[0][0][2]['user_group_name'])
        self.assertEqual(str(self.organization.members[0].id), call_args[0][0][2]['members_select']['initial'][0])

        self.assertEqual(1, len(call_args[0][0][2]['members_select']['options']))
        self.assertEqual(mock_peer_user.get_display_name(),
                         next(iter(call_args[0][0][2]['members_select']['options']))[0])
        self.assertEqual(str(mock_peer_user.id), next(iter(call_args[0][0][2]['members_select']['options']))[1])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.messages')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.reverse')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.redirect')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_handle_manage_member_request_post_remove_orphan_member(self, _, mock_get_app_user_model,
                                                                    __,
                                                                    mock_get_sessionmaker, mock_get_active_app,
                                                                    mock_get_permissions_manager,
                                                                    ___, mock_reverse, mock_messages):

        mock_dict = {'modify-members-submit': 'modify-members-submit',
                     'members-select': [self.app_user]}
        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        make_session = mock_get_sessionmaker()
        session = make_session()

        session.query().get.side_effect = [self.organization, self.app_user]

        app_user.get_app_user_from_request.return_value = self.app_user

        app_user.ROLES.get_no_organization_roles.return_value = [Roles.ORG_ADMIN]

        # call the method
        manage_organization_members = ManageOrganizationMembers()
        manage_organization_members._handle_manage_member_request(mock_request, 'O001')

        # Test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        session.commit.assert_called()
        session.close.assert_called()
        mock_get_active_app.assert_called_with(mock_request)

        mock_get_permissions_manager.assert_called()

        self.assertEqual(mock_request, mock_messages.warning.call_args_list[0][0][0])

        self.assertEqual('Member "{}" was not removed to prevent from being '
                         'orphaned.'.format(self.user_org_member.username),
                         mock_messages.warning.call_args_list[0][0][1])

        self.assertIn('app_users_manage_users', mock_reverse.call_args_list[0][0][0])

    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.render')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_permissions_manager')
    @mock.patch('tethysext.atcore.controllers.app_users.manage_organization_members.get_active_app')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')
    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')
    @mock.patch('tethys_apps.utilities.get_active_app')
    def test_handle_manage_member_request_post_is_client_remove(self, _, mock_get_app_user_model,
                                                                __, mock_get_sessionmaker,
                                                                mock_get_active_app, ___, mock_render):
        mock_dict = {'modify-members-submit': 'modify-members-submit',
                     'members-select': ['0001']}
        mock_request = self.request_factory.post('/foo/bar/map-view/', data=mock_dict)
        mock_request.user = self.django_user

        app_user = mock_get_app_user_model()
        make_session = mock_get_sessionmaker()
        session = make_session()

        app_user.get_app_user_from_request.return_value = self.app_user

        session.query().get.return_value = self.organization

        app_user.ROLES.get_no_organization_roles.return_value = ['Role1']

        # call the method
        manage_organization_members = ManageOrganizationMembers()
        manage_organization_members._handle_manage_member_request(mock_request, 'O001')

        # Test the results
        mock_get_app_user_model().get_app_user_from_request.assert_called_with(mock_request, session)
        app_user.ROLES.get_no_organization_roles.assert_called()
        session.close.assert_called()
        app_user.get_app_user_from_request.assert_called_with(mock_request, session)
        mock_get_active_app.assert_called_with(mock_request)

        call_args = mock_render.call_args_list
        self.assertEqual(mock_request, call_args[0][0][0])
        self.assertEqual('atcore/app_users/manage_organization_members.html', call_args[0][0][1])
        self.assertEqual('0001', call_args[0][0][2]['members_select']['initial'][0])
        self.assertEqual(str(self.app_user.id), call_args[0][0][2]['members_select']['initial'][1])
        self.assertEqual('You cannot remove yourself from this organization.',
                         call_args[0][0][2]['members_select']['error'])
        self.assertEqual('test_organization', call_args[0][0][2]['user_group_name'])

        session.close.assert_called()
