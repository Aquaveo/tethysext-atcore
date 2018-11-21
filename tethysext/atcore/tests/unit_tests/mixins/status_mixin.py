import unittest
import json
from tethysext.atcore.mixins.status_mixin import StatusMixin


class ClassWithStatus(StatusMixin):
    status = None


class StatusMixinTests(unittest.TestCase):

    def setUp(self):
        self.instance = ClassWithStatus()
        self.status_dict = {'foo': StatusMixin.STATUS_SUCCESS}
        self.status_json = json.dumps(self.status_dict)

        self.all_status = [
            StatusMixin.STATUS_AVAILABLE, StatusMixin.STATUS_PENDING, StatusMixin.STATUS_DELETING,
            StatusMixin.STATUS_EMPTY, StatusMixin.STATUS_ERROR, StatusMixin.STATUS_FAILED,
            StatusMixin.STATUS_RESET, StatusMixin.STATUS_NONE, StatusMixin.STATUS_SUCCESS,
            StatusMixin.STATUS_COMPLETE, StatusMixin.STATUS_PROCESSING, StatusMixin.STATUS_WAITING,
            StatusMixin.STATUS_OK, StatusMixin.STATUS_WORKING, StatusMixin.STATUS_UNKNOWN,
            StatusMixin.STATUS_CONTINUE
        ]

    def tearDown(self):
        del self.instance

    def test_get_status_options_list(self):
        self.assertEqual(self.all_status, ClassWithStatus.get_status_options_list())

    def test_get_status_none_no_default(self):
        status = self.instance.get_status('foo')
        self.assertEqual(None, status)
        self.assertIsNone(self.instance.status)

    def test_get_status_none_with_default(self):
        status = self.instance.get_status('foo', 'bar')
        self.assertEqual('bar', status)
        self.assertIsNone(self.instance.status)

    def test_get_status_key_exists(self):
        self.instance.status = self.status_json
        status = self.instance.get_status('foo')
        self.assertEqual(StatusMixin.STATUS_SUCCESS, status)
        self.assertEqual(self.status_json, self.instance.status)

    def test_get_status_key_does_not_exist_with_default(self):
        self.instance.status = self.status_json
        status = self.instance.get_status('bar', 'default-value')
        self.assertEqual('default-value', status)
        self.assertEqual(self.status_json, self.instance.status)

    def test_get_status_key_does_not_exist_no_default(self):
        self.instance.status = self.status_json
        status = self.instance.get_status('bar')
        self.assertEqual(None, status)
        self.assertEqual(self.status_json, self.instance.status)

    def test_set_status_none(self):
        self.instance.set_status('foo', StatusMixin.STATUS_SUCCESS)
        self.assertEqual(self.status_json, self.instance.status)

    def test_set_status_key_exists(self):
        self.instance.status = self.status_json
        self.instance.set_status('foo', StatusMixin.STATUS_ERROR)
        status_json = json.dumps({'foo': StatusMixin.STATUS_ERROR})
        self.assertEqual(status_json, self.instance.status)

    def test_set_status_key_does_not_exist(self):
        self.instance.status = self.status_json
        self.instance.set_status('bar', StatusMixin.STATUS_FAILED)
        status_json = json.dumps({'foo': StatusMixin.STATUS_SUCCESS, 'bar': StatusMixin.STATUS_FAILED})
        self.assertEqual(status_json, self.instance.status)
