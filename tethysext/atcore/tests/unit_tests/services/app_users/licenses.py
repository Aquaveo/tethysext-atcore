import unittest
from tethysext.atcore.services.app_users.licenses import Licenses


class LicensesTests(unittest.TestCase):

    def setUp(self):
        self.licenses = Licenses()
        self.all_licenses = (Licenses.STANDARD, Licenses.ADVANCED, Licenses.PROFESSIONAL, Licenses.CONSULTANT)
        self.invalid_license = 'invalid_license'

    def tearDown(self):
        pass

    def test_licenses(self):
        self.assertEqual('standard', Licenses.STANDARD)
        self.assertEqual('advanced', Licenses.ADVANCED)
        self.assertEqual('professional', Licenses.PROFESSIONAL)
        self.assertEqual('consultant', Licenses.CONSULTANT)

    def test_contains(self):
        self.assertTrue(Licenses.STANDARD in self.licenses)
        self.assertTrue(Licenses.ADVANCED in self.licenses)
        self.assertTrue(Licenses.PROFESSIONAL in self.licenses)
        self.assertTrue(Licenses.CONSULTANT in self.licenses)
        self.assertFalse(self.invalid_license in self.licenses)

    def test_list(self):
        licenses = self.licenses.list()
        self.assertEqual(self.all_licenses, licenses)

    def test_is_valid(self):
        self.assertTrue(self.licenses.is_valid(Licenses.STANDARD))
        self.assertTrue(self.licenses.is_valid(Licenses.ADVANCED))
        self.assertTrue(self.licenses.is_valid(Licenses.PROFESSIONAL))
        self.assertTrue(self.licenses.is_valid(Licenses.CONSULTANT))
        self.assertFalse(self.licenses.is_valid(self.invalid_license))

    def test_get_rank_for(self):
        self.assertEqual(100, self.licenses.get_rank_for(Licenses.STANDARD))
        self.assertEqual(200, self.licenses.get_rank_for(Licenses.ADVANCED))
        self.assertEqual(300, self.licenses.get_rank_for(Licenses.PROFESSIONAL))
        self.assertEqual(400, self.licenses.get_rank_for(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.get_rank_for, self.invalid_license)

    def test_get_display_name_for(self):
        self.assertEqual('Standard', self.licenses.get_display_name_for(Licenses.STANDARD))
        self.assertEqual('Advanced', self.licenses.get_display_name_for(Licenses.ADVANCED))
        self.assertEqual('Professional', self.licenses.get_display_name_for(Licenses.PROFESSIONAL))
        self.assertEqual('Consultant', self.licenses.get_display_name_for(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.get_display_name_for, self.invalid_license)

    def test_get_assign_permission_for(self):
        self.assertEqual('assign_standard_license',
                         self.licenses.get_assign_permission_for(Licenses.STANDARD))
        self.assertEqual('assign_advanced_license',
                         self.licenses.get_assign_permission_for(Licenses.ADVANCED))
        self.assertEqual('assign_professional_license',
                         self.licenses.get_assign_permission_for(Licenses.PROFESSIONAL))
        self.assertEqual('assign_consultant_license', self.licenses.get_assign_permission_for(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.get_assign_permission_for, self.invalid_license)

    def test_compare_standard(self):
        self.assertEqual(Licenses.STANDARD,
                         self.licenses.compare(Licenses.STANDARD, Licenses.STANDARD))
        self.assertEqual(Licenses.ADVANCED,
                         self.licenses.compare(Licenses.STANDARD, Licenses.ADVANCED))
        self.assertEqual(Licenses.PROFESSIONAL,
                         self.licenses.compare(Licenses.STANDARD, Licenses.PROFESSIONAL))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.STANDARD, Licenses.CONSULTANT))

    def test_compare_advanced(self):
        self.assertEqual(Licenses.ADVANCED,
                         self.licenses.compare(Licenses.ADVANCED, Licenses.STANDARD))
        self.assertEqual(Licenses.ADVANCED,
                         self.licenses.compare(Licenses.ADVANCED, Licenses.ADVANCED))
        self.assertEqual(Licenses.PROFESSIONAL,
                         self.licenses.compare(Licenses.ADVANCED, Licenses.PROFESSIONAL))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.ADVANCED, Licenses.CONSULTANT))

    def test_compare_professional(self):
        self.assertEqual(Licenses.PROFESSIONAL,
                         self.licenses.compare(Licenses.PROFESSIONAL, Licenses.STANDARD))
        self.assertEqual(Licenses.PROFESSIONAL,
                         self.licenses.compare(Licenses.PROFESSIONAL, Licenses.ADVANCED))
        self.assertEqual(Licenses.PROFESSIONAL,
                         self.licenses.compare(Licenses.PROFESSIONAL, Licenses.PROFESSIONAL))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.PROFESSIONAL, Licenses.CONSULTANT))

    def test_compare_consultant(self):
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.CONSULTANT, Licenses.STANDARD))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.CONSULTANT, Licenses.ADVANCED))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.CONSULTANT, Licenses.PROFESSIONAL))
        self.assertEqual(Licenses.CONSULTANT,
                         self.licenses.compare(Licenses.CONSULTANT, Licenses.CONSULTANT))

    def test_compare_invalid(self):
        self.assertRaises(ValueError, self.licenses.compare, Licenses.STANDARD, self.invalid_license)
        self.assertRaises(ValueError, self.licenses.compare, self.invalid_license, Licenses.STANDARD)
        self.assertRaises(ValueError, self.licenses.compare, self.invalid_license, self.invalid_license)

    def test_can_have_clients(self):
        self.assertFalse(self.licenses.can_have_clients(Licenses.STANDARD))
        self.assertFalse(self.licenses.can_have_clients(Licenses.ADVANCED))
        self.assertFalse(self.licenses.can_have_clients(Licenses.PROFESSIONAL))
        self.assertTrue(self.licenses.can_have_clients(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.can_have_clients, self.invalid_license)

    def test_can_have_consultant(self):
        self.assertTrue(self.licenses.can_have_consultant(Licenses.STANDARD))
        self.assertTrue(self.licenses.can_have_consultant(Licenses.ADVANCED))
        self.assertTrue(self.licenses.can_have_consultant(Licenses.PROFESSIONAL))
        self.assertFalse(self.licenses.can_have_consultant(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.can_have_consultant, self.invalid_license)

    def test_must_have_consultant(self):
        self.assertFalse(self.licenses.must_have_consultant(Licenses.STANDARD))
        self.assertFalse(self.licenses.must_have_consultant(Licenses.ADVANCED))
        self.assertFalse(self.licenses.must_have_consultant(Licenses.CONSULTANT))
        self.assertFalse(self.licenses.must_have_consultant(Licenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.must_have_consultant, self.invalid_license)
