import unittest
from tethysext.atcore.services.app_users.user_roles import AppUserRoles


class AppUserRoleTests(unittest.TestCase):

    def setUp(self):
        self.user_roles = AppUserRoles()
        self.all_roles = (AppUserRoles.ORG_USER, AppUserRoles.ORG_ADMIN, AppUserRoles.APP_ADMIN, AppUserRoles.DEVELOPER)
        self.invalid_role = 'invalid_role'

    def tearDown(self):
        pass

    def test_roles(self):
        self.assertEqual('user_role_org_user', AppUserRoles.ORG_USER)
        self.assertEqual('user_role_org_admin', AppUserRoles.ORG_ADMIN)
        self.assertEqual('user_role_app_admin', AppUserRoles.APP_ADMIN)
        self.assertEqual('user_role_developer', AppUserRoles.DEVELOPER)

    def test_contains(self):
        self.assertTrue(AppUserRoles.ORG_USER in self.user_roles)
        self.assertTrue(AppUserRoles.ORG_ADMIN in self.user_roles)
        self.assertTrue(AppUserRoles.APP_ADMIN in self.user_roles)
        self.assertTrue(AppUserRoles.DEVELOPER in self.user_roles)
        self.assertFalse(self.invalid_role in self.user_roles)

    def test_list(self):
        roles = self.user_roles.list()
        self.assertEqual(self.all_roles, roles)

    def test_is_valid(self):
        self.assertTrue(self.user_roles.is_valid(AppUserRoles.ORG_USER))
        self.assertTrue(self.user_roles.is_valid(AppUserRoles.ORG_ADMIN))
        self.assertTrue(self.user_roles.is_valid(AppUserRoles.APP_ADMIN))
        self.assertTrue(self.user_roles.is_valid(AppUserRoles.DEVELOPER))
        self.assertFalse(self.user_roles.is_valid(self.invalid_role))

    def test_get_rank_for(self):
        self.assertEqual(100, self.user_roles.get_rank_for(AppUserRoles.ORG_USER))
        self.assertEqual(200, self.user_roles.get_rank_for(AppUserRoles.ORG_ADMIN))
        self.assertEqual(1000, self.user_roles.get_rank_for(AppUserRoles.APP_ADMIN))
        self.assertEqual(float('inf'), self.user_roles.get_rank_for(AppUserRoles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_rank_for, self.invalid_role)

    def test_get_display_name_for(self):
        self.assertEqual('Organization User', self.user_roles.get_display_name_for(AppUserRoles.ORG_USER))
        self.assertEqual('Organization Admin', self.user_roles.get_display_name_for(AppUserRoles.ORG_ADMIN))
        self.assertEqual('App Admin', self.user_roles.get_display_name_for(AppUserRoles.APP_ADMIN))
        self.assertEqual('Developer', self.user_roles.get_display_name_for(AppUserRoles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_display_name_for, self.invalid_role)

    def test_get_assign_permission_for(self):
        self.assertEqual('assign_org_users_role',
                         self.user_roles.get_assign_permission_for(AppUserRoles.ORG_USER))
        self.assertEqual('assign_org_admin_role',
                         self.user_roles.get_assign_permission_for(AppUserRoles.ORG_ADMIN))
        self.assertEqual('assign_app_admin_role',
                         self.user_roles.get_assign_permission_for(AppUserRoles.APP_ADMIN))
        self.assertEqual('assign_developer_role',
                         self.user_roles.get_assign_permission_for(AppUserRoles.DEVELOPER))
        self.assertRaises(ValueError, self.user_roles.get_assign_permission_for, self.invalid_role)

    def test_compare_org_user(self):
        self.assertEqual(AppUserRoles.ORG_USER,
                         self.user_roles.compare(AppUserRoles.ORG_USER, AppUserRoles.ORG_USER))
        self.assertEqual(AppUserRoles.ORG_ADMIN,
                         self.user_roles.compare(AppUserRoles.ORG_USER, AppUserRoles.ORG_ADMIN))
        self.assertEqual(AppUserRoles.APP_ADMIN,
                         self.user_roles.compare(AppUserRoles.ORG_USER, AppUserRoles.APP_ADMIN))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.ORG_USER, AppUserRoles.DEVELOPER))

    def test_compare_org_admin(self):
        self.assertEqual(AppUserRoles.ORG_ADMIN,
                         self.user_roles.compare(AppUserRoles.ORG_ADMIN, AppUserRoles.ORG_USER))
        self.assertEqual(AppUserRoles.ORG_ADMIN,
                         self.user_roles.compare(AppUserRoles.ORG_ADMIN, AppUserRoles.ORG_ADMIN))
        self.assertEqual(AppUserRoles.APP_ADMIN,
                         self.user_roles.compare(AppUserRoles.ORG_ADMIN, AppUserRoles.APP_ADMIN))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.ORG_ADMIN, AppUserRoles.DEVELOPER))

    def test_compare_app_admin(self):
        self.assertEqual(AppUserRoles.APP_ADMIN,
                         self.user_roles.compare(AppUserRoles.APP_ADMIN, AppUserRoles.ORG_USER))
        self.assertEqual(AppUserRoles.APP_ADMIN,
                         self.user_roles.compare(AppUserRoles.APP_ADMIN, AppUserRoles.ORG_ADMIN))
        self.assertEqual(AppUserRoles.APP_ADMIN,
                         self.user_roles.compare(AppUserRoles.APP_ADMIN, AppUserRoles.APP_ADMIN))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.APP_ADMIN, AppUserRoles.DEVELOPER))

    def test_compare_developer(self):
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.DEVELOPER, AppUserRoles.ORG_USER))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.DEVELOPER, AppUserRoles.ORG_ADMIN))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.DEVELOPER, AppUserRoles.APP_ADMIN))
        self.assertEqual(AppUserRoles.DEVELOPER,
                         self.user_roles.compare(AppUserRoles.DEVELOPER, AppUserRoles.DEVELOPER))

    def test_compare_invalid(self):
        self.assertRaises(ValueError, self.user_roles.compareAppUserRoles.ORG_USER, self.invalid_role)
        self.assertRaises(ValueError, self.user_roles.compare, self.invalid_role, AppUserRoles.ORG_USER)
        self.assertRaises(ValueError, self.user_roles.compare, self.invalid_role, self.invalid_role)
