import unittest
from tethysext.atcore.services.app_users.roles import Roles


class AppUserRoleTests(unittest.TestCase):

    def setUp(self):
        self.user_roles = Roles()
        self.all_roles = (Roles.ORG_USER, Roles.ORG_REVIEWER, Roles.ORG_ADMIN, Roles.APP_ADMIN, Roles.DEVELOPER)
        self.invalid_role = 'invalid_role'

    def tearDown(self):
        pass

    def test_roles(self):
        self.assertEqual('user_role_org_user', Roles.ORG_USER)
        self.assertEqual('user_role_org_admin', Roles.ORG_ADMIN)
        self.assertEqual('user_role_app_admin', Roles.APP_ADMIN)
        self.assertEqual('user_role_developer', Roles.DEVELOPER)

    def test_contains(self):
        self.assertTrue(Roles.ORG_USER in self.user_roles)
        self.assertTrue(Roles.ORG_REVIEWER in self.user_roles)
        self.assertTrue(Roles.ORG_ADMIN in self.user_roles)
        self.assertTrue(Roles.APP_ADMIN in self.user_roles)
        self.assertTrue(Roles.DEVELOPER in self.user_roles)
        self.assertFalse(self.invalid_role in self.user_roles)

    def test_list(self):
        roles = self.user_roles.list()
        self.assertEqual(self.all_roles, roles)

    def test_is_valid(self):
        self.assertTrue(self.user_roles.is_valid(Roles.ORG_USER))
        self.assertTrue(self.user_roles.is_valid(Roles.ORG_REVIEWER))
        self.assertTrue(self.user_roles.is_valid(Roles.ORG_ADMIN))
        self.assertTrue(self.user_roles.is_valid(Roles.APP_ADMIN))
        self.assertTrue(self.user_roles.is_valid(Roles.DEVELOPER))
        self.assertFalse(self.user_roles.is_valid(self.invalid_role))

    def test_get_rank_for(self):
        self.assertEqual(100, self.user_roles.get_rank_for(Roles.ORG_USER))
        self.assertEqual(200, self.user_roles.get_rank_for(Roles.ORG_REVIEWER))
        self.assertEqual(300, self.user_roles.get_rank_for(Roles.ORG_ADMIN))
        self.assertEqual(1000, self.user_roles.get_rank_for(Roles.APP_ADMIN))
        self.assertEqual(float('inf'), self.user_roles.get_rank_for(Roles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_rank_for, self.invalid_role)

    def test_get_display_name_for(self):
        self.assertEqual('Organization User', self.user_roles.get_display_name_for(Roles.ORG_USER))
        self.assertEqual('Organization Reviewer', self.user_roles.get_display_name_for(Roles.ORG_REVIEWER))
        self.assertEqual('Organization Admin', self.user_roles.get_display_name_for(Roles.ORG_ADMIN))
        self.assertEqual('App Admin', self.user_roles.get_display_name_for(Roles.APP_ADMIN))
        self.assertEqual('Developer', self.user_roles.get_display_name_for(Roles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_display_name_for, self.invalid_role)

    def test_get_assign_permission_for(self):
        self.assertEqual('assign_org_user_role',
                         self.user_roles.get_assign_permission_for(Roles.ORG_USER))
        self.assertEqual('assign_org_reviewer_role',
                         self.user_roles.get_assign_permission_for(Roles.ORG_REVIEWER))
        self.assertEqual('assign_org_admin_role',
                         self.user_roles.get_assign_permission_for(Roles.ORG_ADMIN))
        self.assertEqual('assign_app_admin_role',
                         self.user_roles.get_assign_permission_for(Roles.APP_ADMIN))
        self.assertEqual('assign_developer_role', self.user_roles.get_assign_permission_for(Roles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_assign_permission_for, self.invalid_role)

    def test_compare_org_user(self):
        self.assertEqual(Roles.ORG_USER,
                         self.user_roles.compare(Roles.ORG_USER, Roles.ORG_USER))
        self.assertEqual(Roles.ORG_ADMIN,
                         self.user_roles.compare(Roles.ORG_USER, Roles.ORG_ADMIN))
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.ORG_USER, Roles.APP_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.ORG_USER, Roles.DEVELOPER))

    def test_compare_org_reviewer(self):
        self.assertEqual(Roles.ORG_REVIEWER,
                         self.user_roles.compare(Roles.ORG_REVIEWER, Roles.ORG_USER))
        self.assertEqual(Roles.ORG_ADMIN,
                         self.user_roles.compare(Roles.ORG_REVIEWER, Roles.ORG_ADMIN))
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.ORG_REVIEWER, Roles.APP_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.ORG_REVIEWER, Roles.DEVELOPER))

    def test_compare_org_admin(self):
        self.assertEqual(Roles.ORG_ADMIN,
                         self.user_roles.compare(Roles.ORG_ADMIN, Roles.ORG_USER))
        self.assertEqual(Roles.ORG_ADMIN,
                         self.user_roles.compare(Roles.ORG_ADMIN, Roles.ORG_ADMIN))
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.ORG_ADMIN, Roles.APP_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.ORG_ADMIN, Roles.DEVELOPER))

    def test_compare_app_admin(self):
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.APP_ADMIN, Roles.ORG_USER))
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.APP_ADMIN, Roles.ORG_ADMIN))
        self.assertEqual(Roles.APP_ADMIN,
                         self.user_roles.compare(Roles.APP_ADMIN, Roles.APP_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.APP_ADMIN, Roles.DEVELOPER))

    def test_compare_developer(self):
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.DEVELOPER, Roles.ORG_USER))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.DEVELOPER, Roles.ORG_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.DEVELOPER, Roles.APP_ADMIN))
        self.assertEqual(Roles.DEVELOPER,
                         self.user_roles.compare(Roles.DEVELOPER, Roles.DEVELOPER))

    def test_compare_invalid(self):
        self.assertRaises(ValueError, self.user_roles.compare, Roles.ORG_USER, self.invalid_role)
        self.assertRaises(ValueError, self.user_roles.compare, self.invalid_role, Roles.ORG_USER)
        self.assertRaises(ValueError, self.user_roles.compare, self.invalid_role, self.invalid_role)

    def test_get_organization_required_roles(self):
        out = self.user_roles.get_organization_required_roles()
        self.assertEqual(3, len(out))
        self.assertListEqual([self.user_roles.ORG_USER, self.user_roles.ORG_REVIEWER, self.user_roles.ORG_ADMIN], out)

    def test_get_no_organization_roles(self):
        out = self.user_roles.get_no_organization_roles()
        self.assertEqual(2, len(out))
        self.assertListEqual([self.user_roles.APP_ADMIN, self.user_roles.DEVELOPER], out)
