import uuid
from unittest.mock import patch
from tethysext.atcore.models.app_users import Organization, AppUser, Resource
from tethysext.atcore.tests.mock.permissions import mock_has_permission_false
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class OrganizationTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.name = "test_organization"
        self.active = True
        self.license = Organization.LICENSES.STANDARD
        self.invalid_license = 'invalid-license'
        self.mock_request = object()

        self.organization = Organization(
            name=self.name,
            active=self.active,
            license=self.license
        )

        self.session.add(self.organization)

        self.staff_user = AppUser(
            username=AppUser.STAFF_USERNAME,
            role=AppUser.STAFF_ROLE
        )
        self.normal_user = AppUser(
            username="orguser",
            role=AppUser.ROLES.ORG_USER
        )
        self.organization.members.extend([self.staff_user, self.normal_user])

        self.non_member_user = AppUser(
            username='nonmember',
            role=AppUser.ROLES.ORG_USER
        )

        self.resource = Resource(
            name="res1"
        )
        self.organization.resources.append(self.resource)

        self.session.commit()
        self.organization_id = self.organization.id
        self.staff_user_id = self.staff_user.id
        self.normal_user_id = self.normal_user.id
        self.resource_id = self.resource.id

    def test_create_organization(self):
        organization = Organization(
            name=self.name,
            active=self.active,
            license=Organization.LICENSES.STANDARD
        )

        self.session.add(organization)
        self.session.commit()

        self.assertEqual(organization.name, self.name)
        self.assertEqual(organization.active, self.active)
        self.assertEqual(self.license, organization.license)
        self.assertEqual(organization.type, Organization.TYPE)
        self.assertIsInstance(organization.id, uuid.UUID)

    def test_validate_license(self):
        self.organization.license = Organization.LICENSES.STANDARD
        self.organization.license = Organization.LICENSES.ADVANCED
        self.organization.license = Organization.LICENSES.PROFESSIONAL
        self.organization.license = Organization.LICENSES.CONSULTANT
        exception_raised = False
        try:
            self.organization.license = self.invalid_license
        except Exception as e:
            exception_raised = True
            self.assertIsInstance(e, ValueError)
        self.assertTrue(exception_raised)

    def test_get_create_permission(self):
        perm = self.organization.get_create_permission()
        self.assertEqual('create_organizations', perm)

    def test_get_edit_permission(self):
        perm = self.organization.get_edit_permission()
        self.assertEqual('edit_organizations', perm)

    def test_get_delete_permission(self):
        perm = self.organization.get_delete_permission()
        self.assertEqual('delete_organizations', perm)

    def test_get_modify_member_permission(self):
        perm = self.organization.get_modify_members_permission()
        self.assertEqual('modify_organization_members', perm)

    @patch('tethys_sdk.permissions.has_permission', side_effect=mock_has_permission_false)
    def test_update_member_activity(self, mock_has_permission_function):
        self.organization.active = False
        self.organization.update_member_activity(self.session, self.mock_request)
        self.session.commit()
        self.assertFalse(self.normal_user.is_active)
        self.assertTrue(self.staff_user.is_active)

        self.organization.active = True
        self.organization.update_member_activity(self.session, self.mock_request)
        self.session.commit()
        self.assertTrue(self.normal_user.is_active)
        self.assertTrue(self.staff_user.is_active)

    def test_can_add_client_with_license_standard(self):
        self.organization.license = Organization.LICENSES.STANDARD
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.STANDARD)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.ADVANCED)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.PROFESSIONAL)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.CONSULTANT)
        self.assertFalse(out)

    def test_can_add_client_with_license_advanced(self):
        self.organization.license = Organization.LICENSES.ADVANCED
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.STANDARD)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.ADVANCED)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.PROFESSIONAL)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.CONSULTANT)
        self.assertFalse(out)

    def test_can_add_client_with_license_professional(self):
        self.organization.license = Organization.LICENSES.PROFESSIONAL
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.STANDARD)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.ADVANCED)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.PROFESSIONAL)
        self.assertFalse(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.CONSULTANT)
        self.assertFalse(out)

    def test_can_add_client_with_license_Consultant(self):
        self.organization.license = Organization.LICENSES.CONSULTANT
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.STANDARD)
        self.assertTrue(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.ADVANCED)
        self.assertTrue(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.PROFESSIONAL)
        self.assertTrue(out)
        out = self.organization.can_add_client_with_license(self.session, self.mock_request,
                                                            Organization.LICENSES.CONSULTANT)
        self.assertTrue(out)

    def test_can_add_client_with_license_invalid(self):
        self.assertRaises(ValueError, self.organization.can_add_client_with_license, self.session,
                          self.mock_request, self.invalid_license)

    def test_can_have_clients(self):
        self.organization.license = Organization.LICENSES.STANDARD
        out = self.organization.can_have_clients()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.ADVANCED
        out = self.organization.can_have_clients()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.PROFESSIONAL
        out = self.organization.can_have_clients()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.CONSULTANT
        out = self.organization.can_have_clients()
        self.assertTrue(out)

    def test_can_have_consultant(self):
        self.organization.license = Organization.LICENSES.STANDARD
        out = self.organization.can_have_consultant()
        self.assertTrue(out)
        self.organization.license = Organization.LICENSES.ADVANCED
        out = self.organization.can_have_consultant()
        self.assertTrue(out)
        self.organization.license = Organization.LICENSES.PROFESSIONAL
        out = self.organization.can_have_consultant()
        self.assertTrue(out)
        self.organization.license = Organization.LICENSES.CONSULTANT
        out = self.organization.can_have_consultant()
        self.assertFalse(out)

    def test_must_have_consultant(self):
        self.organization.license = Organization.LICENSES.STANDARD
        out = self.organization.must_have_consultant()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.ADVANCED
        out = self.organization.must_have_consultant()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.PROFESSIONAL
        out = self.organization.must_have_consultant()
        self.assertFalse(out)
        self.organization.license = Organization.LICENSES.CONSULTANT
        out = self.organization.must_have_consultant()
        self.assertFalse(out)

    def test_receive_before_delete(self):
        self.session.delete(self.organization)
        self.session.commit()
        staff_user = self.session.query(AppUser).filter(AppUser.id == self.staff_user_id).one_or_none()
        self.assertIsNotNone(staff_user)

        normal_user = self.session.query(AppUser).filter(AppUser.id == self.normal_user_id).one_or_none()
        self.assertIsNone(normal_user)

        resource = self.session.query(Resource).filter(Resource.id == self.resource_id).one_or_none()
        self.assertIsNone(resource)

    def test_is_member_true(self):
        ret = self.organization.is_member(self.normal_user)
        self.assertTrue(ret)

    def test_is_member_false(self):
        ret = self.organization.is_member(self.non_member_user)
        self.assertFalse(ret)
