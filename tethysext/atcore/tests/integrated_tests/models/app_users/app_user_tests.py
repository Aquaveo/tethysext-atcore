import uuid
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from tethys_sdk.base import TethysController
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.models.app_users.user_setting import UserSetting
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.mock.django import MockDjangoRequest
from tethysext.atcore.tests.mock.permissions import mock_has_permission_false, mock_has_permission_assignable_roles, \
    mock_has_permission_true
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


class CustomOrganization(Organization):
    TYPE = 'testing__custom_organization__testing'
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }


class CustomResource(Resource):
    TYPE = 'testing_custom_resource_1__testing'

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE,
    }


class CustomAppUser(AppUser):
    @staticmethod
    def get_organization_model():
        return CustomOrganization

    @staticmethod
    def get_resource_model():
        return CustomResource


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class TestController(TethysController):
    pass


class AppUserTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.role = Roles.ORG_USER
        self.is_active = True

        self.user = AppUser(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
        )
        app_admin_username = "app_admin_user"
        self.app_admin_user = AppUser(
            username=app_admin_username,
            role=Roles.APP_ADMIN,
            is_active=self.is_active,
        )
        self.peer_user = AppUser(
            username="user1",
            role=self.role,
            is_active=self.is_active,
        )
        self.client_user = AppUser(
            username="user2",
            role=self.role,
            is_active=self.is_active,
        )
        self.foreign_user = AppUser(
            username="user3",
            role=self.role,
            is_active=self.is_active,
        )

        self.session.add(self.user)
        self.session.commit()
        self.user_id = self.user.id

        self.org1_name = "Org1"
        self.org2_name = "Org2"
        self.org3_name = "Org3"

        self.org1 = Organization(
            name=self.org1_name,
            license=Organization.LICENSES.CONSULTANT
        )
        self.org1.members.append(self.user)
        self.org1.members.append(self.peer_user)

        self.org2 = Organization(
            name=self.org2_name,
            license=Organization.LICENSES.STANDARD
        )
        self.org2.members.append(self.client_user)

        self.org2.consultant = self.org1

        self.org3 = Organization(
            name=self.org3_name,
            license=Organization.LICENSES.STANDARD
        )
        self.org3.members.append(self.foreign_user)

        self.session.add(self.org1)
        self.session.add(self.org2)
        self.session.add(self.org3)
        self.session.commit()

        self.rsrc1_name = 'Resource1'
        self.rsrc2_name = 'Resource2'
        self.rsrc3_name = 'Resource3'

        self.rsrc1 = Resource(
            name=self.rsrc1_name,
            description='',
            status=Resource.STATUS_NONE
        )
        self.rsrc1.organizations.append(self.org1)

        self.rsrc2 = CustomResource(
            name=self.rsrc2_name,
            description='',
            status=Resource.STATUS_NONE,
        )
        self.rsrc2.organizations.append(self.org2)

        self.rsrc3 = Resource(
            name=self.rsrc3_name,
            description='',
            status=Resource.STATUS_NONE
        )
        self.rsrc3.organizations.append(self.org3)

        self.django_user = User.objects.create_user(
            username=self.username,
            password="pass"
        )
        self.app_admin_django_user = User.objects.create_user(
            username=app_admin_username,
            password="pass"
        )

        self.session.add(self.rsrc1)
        self.session.add(self.rsrc2)
        self.session.add(self.rsrc3)
        self.session.commit()

        self.staff_user = self.session.query(AppUser). \
            filter(AppUser.username == AppUser.STAFF_USERNAME). \
            one()

        self.staff_user_request = MockDjangoRequest(
            user_username="im_staff",
            user_is_staff=True
        )

        self.user_request = MockDjangoRequest(
            user_username=self.username,
            user_is_staff=False
        )

        self.app_admin_user_request = MockDjangoRequest(
            user_username=app_admin_username,
            user_is_staff=False
        )

    def test_create_user(self):
        user = self.session.query(AppUser).get(self.user_id)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.role, self.role)
        self.assertEqual(user.is_active, self.is_active)
        self.assertIsNotNone(user.id)
        self.assertIsInstance(user.id, uuid.UUID)

    def test_get_django_user_existing(self):
        returned_django_user = self.user.get_django_user()
        self.assertEqual(self.django_user, returned_django_user)

    def test_get_django_user_non_existing(self):
        user = User.objects.get(username=self.username)
        User.delete(user)
        returned_django_user = self.user.get_django_user()
        self.assertIsNone(returned_django_user)

    def test_validate_role_valid(self):
        self.user.role = AppUser.ROLES.ORG_ADMIN
        self.assertEqual(AppUser.ROLES.ORG_ADMIN, self.user.role)

    def test_validate_role_invalid(self):
        exception_thrown = False
        try:
            self.user.role = 'invalid-role'
        except Exception as e:
            exception_thrown = True
            self.assertIsInstance(e, ValueError)
        self.assertTrue(exception_thrown)

    def test_django_user_property(self):
        self.assertIsNone(self.user._django_user)
        retrieved_django_user = self.user.django_user
        self.assertIsNotNone(self.user._django_user)
        self.assertEqual(retrieved_django_user, self.user._django_user)
        self.assertEqual(self.django_user, retrieved_django_user)

    def test_django_user_property_staff(self):
        self.assertIsNone(self.staff_user._django_user)
        retrieved_django_user = self.staff_user.django_user
        self.assertIsNone(self.staff_user._django_user)
        self.assertEqual(retrieved_django_user, self.staff_user._django_user)

    def test_get_app_user_from_request(self):
        app_user = AppUser.get_app_user_from_request(self.user_request, self.session)

        self.assertIsNotNone(app_user)
        self.assertEqual(self.username, app_user.username)
        self.assertEqual(self.user_id, app_user.id)

    def test_get_app_user_from_request_staff(self):
        app_user = AppUser.get_app_user_from_request(self.staff_user_request, self.session)

        self.assertIsNotNone(app_user)
        self.assertEqual(AppUser.STAFF_USERNAME, app_user.username)

    def test_get_organization_model_default(self):
        organization_model = AppUser.get_organization_model()
        self.assertEqual(Organization, organization_model)

    def test_get_organization_model_overriden(self):
        organization_model = CustomAppUser.get_organization_model()
        self.assertEqual(CustomOrganization, organization_model)

    def test_get_resource_model_default(self):
        resource_model = AppUser.get_resource_model()
        self.assertEqual(Resource, resource_model)

    def test_get_resource_model_overriden(self):
        resource_model = CustomAppUser.get_resource_model()
        self.assertEqual(CustomResource, resource_model)

    def test_is_staff_true(self):
        self.assertTrue(self.staff_user.is_staff())

    def test_is_staff_false(self):
        self.assertFalse(self.user.is_staff())

    def test_get_display_name_staff(self):
        display_name = self.staff_user.get_display_name()
        self.assertEqual(AppUser.STAFF_DISPLAY_NAME, display_name)

    def test_get_display_name_first_last(self):
        firstname = "foo"
        lastname = "bar"
        display_name = " ".join([firstname, lastname])
        self.django_user.first_name = firstname
        self.django_user.last_name = lastname
        self.django_user.save()

        self.assertEqual(display_name, self.user.get_display_name())

    def test_get_display_name_first_only(self):
        firstname = "foo"
        display_name = firstname
        self.django_user.first_name = firstname
        self.django_user.save()

        self.assertEqual(display_name, self.user.get_display_name())

    def test_get_display_name_last_only(self):
        lastname = "bar"
        display_name = lastname
        self.django_user.last_name = lastname
        self.django_user.save()

        self.assertEqual(display_name, self.user.get_display_name())

    def test_get_display_name_no_first_last(self):
        display_name = self.username
        self.assertEqual(display_name, self.user.get_display_name())

    def test_get_display_name_append_username(self):
        firstname = "foo"
        lastname = "bar"
        display_name = " ".join([firstname, lastname]) + " ({})".format(self.username)
        self.django_user.first_name = firstname
        self.django_user.last_name = lastname
        self.django_user.save()

        self.assertEqual(display_name, self.user.get_display_name(append_username=True))

    def test_get_display_name_not_default_to_username(self):
        display_name = ""
        self.assertEqual(display_name, self.user.get_display_name(default_to_username=False))

    def test_get_organizations_staff(self):
        organizations = self.staff_user.get_organizations(self.session, self.staff_user_request)
        self.assertEqual(3, len(organizations))

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_organizations(self, mock_has_permission_function):
        organizations = self.user.get_organizations(self.session, self.user_request)
        self.assertEqual(2, len(organizations))
        expected_names = [self.org1_name, self.org2_name]
        for org in organizations:
            self.assertIn(org.name, expected_names)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_organizations_no_cascade(self, mock_has_permission_function):
        organizations = self.user.get_organizations(self.session, self.user_request, cascade=False)
        self.assertEqual(1, len(organizations))
        for org in organizations:
            self.assertEqual(self.org1_name, org.name)

    def test_get_organizations_as_options(self):
        organizations = self.staff_user.get_organizations(self.session, self.staff_user_request, as_options=True)
        self.assertEqual(3, len(organizations))
        expected_options = [
            (self.org1_name, str(self.org1.id)),
            (self.org2_name, str(self.org2.id)),
            (self.org3_name, str(self.org3.id)),
        ]
        for org_options in organizations:
            self.assertIn(org_options, expected_options)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_organizations_consultants(self, mock_has_permission_function):
        organizations = self.user.get_organizations(self.session, self.user_request, consultants=True)
        self.assertEqual(1, len(organizations))
        for org in organizations:
            self.assertEqual(self.org1_name, org.name)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_true)
    def test_get_resources_staff(self, mock_has_permission_function):
        resources = self.staff_user.get_resources(self.session, self.staff_user_request)
        self.assertEqual(3, len(resources))

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_resources(self, mock_has_permission_function):
        resources = self.user.get_resources(self.session, self.user_request)
        self.assertEqual(2, len(resources))
        expected_names = [self.rsrc1_name, self.rsrc2_name]
        for rsrc in resources:
            self.assertIn(rsrc.name, expected_names)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_resources_for_assigning(self, mock_has_permission_function):
        resources = self.user.get_resources(self.session, self.user_request, for_assigning=True)
        self.assertEqual(2, len(resources))
        expected_names = [self.rsrc1_name, self.rsrc2_name]
        for rsrc in resources:
            self.assertIn(rsrc.name, expected_names)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_resources_no_cascade(self, mock_has_permission_function):
        resources = self.user.get_resources(self.session, self.user_request, cascade=False)
        self.assertEqual(1, len(resources))
        for rsrc in resources:
            self.assertEqual(self.rsrc1_name, rsrc.name)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_resources_of_type(self, mock_has_permission_function):
        resources = self.user.get_resources(self.session, self.user_request, of_type=CustomResource)
        self.assertEqual(1, len(resources))
        for rsrc in resources:
            self.assertEqual(self.rsrc2_name, rsrc.name)

    def test_filter_resources(self):
        in_resources = [self.rsrc1, self.rsrc2, self.rsrc3]
        out_resources = self.user.filter_resources(in_resources)
        self.assertEqual(in_resources, out_resources)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_assignable_roles)
    def test_get_assignable_roles(self, mock_has_permission_function):
        assignable_roles = self.user.get_assignable_roles(self.user_request)
        self.assertEqual(2, len(assignable_roles))
        expected_roles = [AppUser.ROLES.ORG_USER, AppUser.ROLES.ORG_ADMIN]
        for role in assignable_roles:
            self.assertIn(role, expected_roles)

    def test_get_assignable_roles_staff(self):
        assignable_roles = self.staff_user.get_assignable_roles(self.user_request)
        expected_roles = list(AppUser.ROLES.list())
        self.assertEqual(expected_roles, assignable_roles)

    def test_get_assignable_roles_as_options(self):
        assignable_options = self.staff_user.get_assignable_roles(self.user_request, as_options=True)
        all_roles = AppUser.ROLES.list()
        expected_options = [(AppUser.ROLES.get_display_name_for(r), r) for r in all_roles]
        self.assertEqual(expected_options, assignable_options)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_peers(self, mock_has_permission_function):
        peers = self.user.get_peers(self.session, self.user_request)
        self.assertIn(self.peer_user, peers, "Peer user not found in peers.")
        self.assertNotIn(self.client_user, peers, "Client user found in peers.")
        self.assertNotIn(self.foreign_user, peers, "Peer user found in peers.")
        self.assertNotIn(self.user, peers, "User found in peers.")

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_peers_include_self(self, mock_has_permission_function):
        peers = self.user.get_peers(self.session, self.user_request, include_self=True)
        self.assertIn(self.peer_user, peers, "Peer user not found in peers.")
        self.assertNotIn(self.client_user, peers, "Client user found in peers.")
        self.assertNotIn(self.foreign_user, peers, "Peer user found in peers.")
        self.assertIn(self.user, peers, "User not found in peers.")

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_peers_cascade(self, mock_has_permission_function):
        peers = self.user.get_peers(self.session, self.user_request, cascade=True)
        self.assertIn(self.peer_user, peers, "Peer user not found in peers.")
        self.assertIn(self.client_user, peers, "Client user not found in peers.")
        self.assertNotIn(self.foreign_user, peers, "Peer user found in peers.")
        self.assertNotIn(self.user, peers, "User found in peers.")

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_get_peers_staff(self, mock_has_permission_function):
        peers = self.staff_user.get_peers(self.session, self.staff_user_request)
        self.assertIn(self.peer_user, peers, "Peer user not found in peers.")
        self.assertIn(self.client_user, peers, "Client user not found in peers.")
        self.assertIn(self.foreign_user, peers, "Peer user not found in peers.")
        self.assertIn(self.user, peers, "Staff user not found in peers.")
        self.assertNotIn(self.staff_user, peers, "Staff user found in peers.")

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_update_activity(self, mock_has_permission_function):
        self.org1.active = False
        self.user.update_activity(self.session, self.user_request)
        self.session.commit()
        self.assertFalse(self.user.is_active)

        self.org1.active = True
        self.user.update_activity(self.session, self.user_request)
        self.session.commit()
        self.assertTrue(self.user.is_active)

    def test_update_activity_staff(self):
        self.org1.members.append(self.staff_user)
        self.org1.active = False
        self.session.commit()
        self.staff_user.update_activity(self.session, self.staff_user_request)
        self.assertTrue(self.staff_user.is_active)

    def test_get_role(self):
        role = self.user.get_role()
        self.assertEqual(self.user.role, role)

    def test_get_role_display_name(self):
        role = self.user.get_role(display_name=True)
        display_name = self.user.ROLES.get_display_name_for(self.user.role)
        self.assertEqual(display_name, role)

    def test_get_user_setting_model(self):
        _user_setting = self.user._get_user_setting_model()
        self.assertEqual(UserSetting, _user_setting)

    def test_email_getter(self):
        email = self.user.email
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.email, email)
        self.assertEqual(django_user.email, email)

    def test_email_setter(self):
        email = "user@aquaveo.com"
        self.user.email = email
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.email, email)
        self.assertEqual(django_user.email, email)

    def test_first_name_getter(self):
        first_name = self.user.first_name
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.first_name, first_name)
        self.assertEqual(django_user.first_name, first_name)

    def test_first_name_setter(self):
        first_name = "foo"
        self.user.first_name = first_name
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.first_name, first_name)
        self.assertEqual(django_user.first_name, first_name)

    def test_last_name_getter(self):
        last_name = self.user.last_name
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.last_name, last_name)
        self.assertEqual(django_user.last_name, last_name)

    def test_last_name_setter(self):
        last_name = "foo"
        self.user.last_name = last_name
        django_user = User.objects.get(pk=self.django_user.id)
        self.assertEqual(self.user.django_user.last_name, last_name)
        self.assertEqual(django_user.last_name, last_name)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    @patch("tethysext.atcore.services.app_users.permissions_manager.AppPermissionsManager")
    def test_update_permissions(self, MockAppPermissionsManager, mock_has_permission_function):
        mapm = MockAppPermissionsManager("foo")
        mapm.remove_all_permissions_groups = MagicMock()
        mapm.assign_user_permission = MagicMock()
        self.user.update_permissions(self.session, self.user_request, mapm)
        mapm.remove_all_permissions_groups.assert_called()
        mapm.assign_user_permission.assert_called_with(self.user, self.user.role, self.org1.license)

    @patch("tethysext.atcore.services.app_users.permissions_manager.AppPermissionsManager")
    def test_update_permissions_no_org_roles(self, MockAppPermissionsManager):
        mapm = MockAppPermissionsManager("foo")
        mapm.remove_all_permissions_groups = MagicMock()
        mapm.assign_user_permission = MagicMock()
        self.app_admin_user.update_permissions(self.session, self.app_admin_user_request, mapm)
        mapm.remove_all_permissions_groups.assert_called()
        mapm.assign_user_permission.assert_called_with(self.app_admin_user, self.app_admin_user.role,
                                                       Organization.LICENSES.NONE)

    def test_get_rank_single_permissions_group(self):
        apm = AppPermissionsManager("foo")
        apm.get_all_permissions_groups_for = MagicMock(
            return_value=[apm.STANDARD_USER_PERMS]
        )
        rank = self.user.get_rank(apm)
        apm.get_all_permissions_groups_for.assert_called()
        self.assertEqual(1100.0, rank)

    def test_get_rank_multiple_permissions_groups(self):
        apm = AppPermissionsManager("foo")
        apm.get_all_permissions_groups_for = MagicMock(
            return_value=[apm.STANDARD_USER_PERMS, apm.STANDARD_ADMIN_PERMS]
        )
        rank = self.user.get_rank(apm)
        apm.get_all_permissions_groups_for.assert_called()
        self.assertEqual(1300.0, rank)

    def _init_settings_same_keys(self):
        setting1 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )

        setting2 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='2',
        )
        a = UserSetting.build_attributes(page='a_page')
        setting2.attributes = a

        setting3 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='3',
        )
        a = UserSetting.build_attributes(resource=self.rsrc1)
        setting3.attributes = a

        setting4 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='4',
        )
        a = UserSetting.build_attributes(secondary_id='another-id')
        setting4.attributes = a

        self.session.add_all([setting1, setting2, setting3, setting4])
        self.session.commit()
        return [setting1, setting2, setting3, setting4]

    def _init_settings_same_keys_same_values(self):
        setting1 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )

        setting2 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )
        a = UserSetting.build_attributes(page='a_page')
        setting2.attributes = a

        setting3 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )
        a = UserSetting.build_attributes(resource=self.rsrc1)
        setting3.attributes = a

        setting4 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )
        a = UserSetting.build_attributes(secondary_id='another-id')
        setting4.attributes = a

        self.session.add_all([setting1, setting2, setting3, setting4])
        self.session.commit()
        return [setting1, setting2, setting3, setting4]

    def _init_settings_different_keys(self):
        setting1 = UserSetting(
            user_id=self.user.id,
            key='one',
            value='1',
        )
        setting2 = UserSetting(
            user_id=self.user.id,
            key='two',
            value='1',
        )
        a = UserSetting.build_attributes(page='a_page')
        setting2.attributes = a

        setting3 = UserSetting(
            user_id=self.user.id,
            key='three',
            value='1',
        )
        a = UserSetting.build_attributes(resource=self.rsrc1)
        setting3.attributes = a

        setting4 = UserSetting(
            user_id=self.user.id,
            key='three',
            value='1',
        )
        a = UserSetting.build_attributes(secondary_id='another-id')
        setting4.attributes = a

        self.session.add_all([setting1, setting2, setting3, setting4])
        self.session.commit()
        return [setting1, setting2, setting3, setting4]

    def test_get_setting(self):
        setting = UserSetting(
            user_id=self.user.id,
            key='foo',
            value='bar'
        )
        self.session.add(setting)
        self.session.commit()
        return_val = self.user.get_setting(self.session, key='foo')
        self.assertIsInstance(return_val, UserSetting)
        self.assertEqual('bar', return_val.value)

    def test_get_setting_no_setting(self):
        return_val = self.user.get_setting(self.session, key='foo')
        self.assertIsNone(return_val)

    def test_get_setting_multiple_same_key(self):
        self._init_settings_same_keys()
        return_val = self.user.get_setting(self.session, 'one')
        self.assertIsInstance(return_val, UserSetting)
        self.assertEqual('1', return_val.value)

    def test_get_setting_as_value(self):
        setting = UserSetting(
            user_id=self.user.id,
            key='foo',
            value='bar'
        )
        self.session.add(setting)
        self.session.commit()
        return_val = self.user.get_setting(self.session, key='foo', as_value=True)
        self.assertEqual('bar', return_val)

    def test_get_setting_resource(self):
        setting = UserSetting(
            user_id=self.user.id,
            key='foo',
            value='bar',
        )
        a = UserSetting.build_attributes(resource=self.rsrc1)
        setting.attributes = a

        self.session.add(setting)
        self.session.commit()
        return_val = self.user.get_setting(self.session, key='foo', resource=self.rsrc1)
        self.assertIsInstance(return_val, UserSetting)
        self.assertEqual('bar', return_val.value)

    def test_get_setting_page(self):
        setting = UserSetting(
            user_id=self.user.id,
            key='foo',
            value='bar',
        )
        a = UserSetting.build_attributes(page='a_page')
        setting.attributes = a

        self.session.add(setting)
        self.session.commit()
        return_val = self.user.get_setting(self.session, key='foo', page='a_page')
        self.assertIsInstance(return_val, UserSetting)
        self.assertEqual('bar', return_val.value)

    def test_get_setting_secondary_id(self):
        setting = UserSetting(
            user_id=self.user.id,
            key='foo',
            value='bar',
        )
        a = UserSetting.build_attributes(secondary_id='another-id')
        setting.attributes = a

        self.session.add(setting)
        self.session.commit()
        return_val = self.user.get_setting(self.session, key='foo', secondary_id='another-id')
        self.assertIsInstance(return_val, UserSetting)
        self.assertEqual('bar', return_val.value)

    def test_get_all_settings(self):
        self._init_settings_different_keys()
        return_val = self.user.get_all_settings(self.session)
        self.assertIsNotNone(return_val)
        self.assertEqual(4, len(return_val))

    def test_delete_existing_settings(self):
        settings = self._init_settings_same_keys()
        settings_to_delete = [settings[0], settings[2]]
        self.user.delete_existing_settings(self.session, settings_to_delete)
        count = self.session.query(UserSetting).count()
        self.assertEqual(2, count)

    def test_update_setting(self):
        self._init_settings_same_keys_same_values()
        self.user.update_setting(self.session, 'one', '2')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))

    def test_update_setting_non_existing(self):
        self.user.update_setting(self.session, 'one', '2')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))

    def test_update_setting_resource(self):
        self._init_settings_same_keys_same_values()
        self.user.update_setting(self.session, 'one', '2', resource=self.rsrc1)
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))

    def test_update_setting_secondary_id(self):
        self._init_settings_same_keys_same_values()
        self.user.update_setting(self.session, 'one', '2', secondary_id='another-id')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))

    def test_update_setting_page(self):
        self._init_settings_same_keys_same_values()
        self.user.update_setting(self.session, 'one', '2', page='a_page')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))

    def test_update_setting_no_commit(self):
        self._init_settings_same_keys_same_values()
        self.user.update_setting(self.session, 'one', '2', commit=False)
        self.session.rollback()
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(0, len(settings))

    def test_update_setting_multiple_times(self):
        self.user.update_setting(self.session, 'one', '1')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '1').all()
        self.assertEqual(1, len(settings))
        self.user.update_setting(self.session, 'one', '2')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '2').all()
        self.assertEqual(1, len(settings))
        self.user.update_setting(self.session, 'one', '3')
        settings = self.session.query(UserSetting).filter(UserSetting.value == '3').all()
        self.assertEqual(1, len(settings))
        all_one_settings = self.session.query(UserSetting).filter(UserSetting.key == 'one').all()
        self.assertEqual(1, len(all_one_settings))

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_can_view_direct_true(self, mock_has_permission_function):
        return_val = self.user.can_view(self.session, self.user_request, self.rsrc1)
        self.assertTrue(return_val)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_can_view_client_true(self, mock_has_permission_function):
        return_val = self.user.can_view(self.session, self.user_request, self.rsrc2)
        self.assertTrue(return_val)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_can_view_false(self, mock_has_permission_function):
        return_val = self.user.can_view(self.session, self.user_request, self.rsrc3)
        self.assertFalse(return_val)
