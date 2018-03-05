from tethys_sdk.testing import TethysTestCase


class OneTestCaseClass(TethysTestCase):
    def set_up(self):
        self.user = self.create_test_user(username="joe", email="joe@some_site.com", password="secret")
        self.c = self.get_test_client()

    def tear_down(self):
        pass

    def test_test_1(self):
        print "test1"
        self.c.force_login(self.user)
        response = self.c.get('/extensions/atcore/foo')
        self.assertEqual(response.status_code, 404)
        self.assertIsNotNone(response.context)
