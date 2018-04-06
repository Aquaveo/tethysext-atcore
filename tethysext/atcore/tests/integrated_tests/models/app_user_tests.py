import uuid

from django.contrib.auth.models import User
from mock import patch
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.models.app_users import initialize_app_users_db
from tethysext.atcore.services.app_users.user_roles import Roles
from tethysext.atcore.tests import APP_USER_TEST_DB
from tethysext.atcore.tests.mock.django import MockDjangoRequest
from tethysext.atcore.tests.mock.permissions import mock_has_permission_false, mock_has_permission_assignable_roles


class CustomOrganization(Organization):
    pass


class CustomResource(Resource):
    TYPE = 'custom_type'

    # Polymorphism
    __mapper_args__ = {
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
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(APP_USER_TEST_DB)
    connection = engine.connect()
    transaction = connection.begin()
    # Initialize db with staff user
    initialize_app_users_db(connection)


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class AppUserTests(TethysTestCase):

    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.username = "test_user"
        self.role = Roles.ORG_USER
        self.is_active = True

        self.user = AppUser(
            username=self.username,
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
            license=Organization.LICENSES.STANDARD
        )
        self.org1.members.append(self.user)

        self.org2 = Organization(
            name=self.org2_name,
            license=Organization.LICENSES.STANDARD
        )

        self.org2.consultant = self.org1

        self.org3 = Organization(
            name=self.org3_name,
            license=Organization.LICENSES.STANDARD
        )

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
            password="pass",
        )

        self.session.add(self.rsrc1)
        self.session.add(self.rsrc2)
        self.session.add(self.rsrc3)
        self.session.commit()

        self.staff_user = self.session.query(AppUser).\
            filter(AppUser.username == AppUser.STAFF_USERNAME).\
            one()

        self.staff_user_request = MockDjangoRequest(
            user_username="im_staff",
            user_is_staff=True
        )

        self.user_request = MockDjangoRequest(
            user_username=self.username,
            user_is_staff=False
        )

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_create_user(self):
        user = self.session.query(AppUser).get(self.user_id)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.role, self.role)
        self.assertEqual(user.is_active, self.is_active)
        self.assertIsNotNone(user.id)
        self.assertIsInstance(user.id, uuid.UUID)

    def test_get_django_user_existing(self):
        returned_django_user = self.user.get_django_user()
        self.assertEquals(self.django_user, returned_django_user)

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

    def test_get_resources_staff(self):
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
