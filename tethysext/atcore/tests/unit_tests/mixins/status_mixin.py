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
            StatusMixin.STATUS_CONTINUE, StatusMixin.STATUS_UNDER_REVIEW, StatusMixin.STATUS_SUBMITTED,
            StatusMixin.STATUS_APPROVED, StatusMixin.STATUS_REJECTED, StatusMixin.STATUS_CHANGES_REQUESTED,
            StatusMixin.STATUS_DIRTY
        ]

    def tearDown(self):
        del self.instance

    def test_valid_statuses(self):
        self.assertEqual(self.all_status, ClassWithStatus.valid_statuses())

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

    def test_set_status(self):
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

    def test_set_status_invalid(self):
        self.assertRaises(ValueError, self.instance.set_status, 'foo', 'invalid-status')

    def test_set_status_none(self):
        expected_status_json = json.dumps({'foo': None})

        self.instance.set_status('foo', None)

        self.assertEqual(expected_status_json, self.instance.status)
        get_status_failed = False

        try:
            ret = self.instance.get_status('foo')
            self.assertIsNone(ret)
        except Exception:
            get_status_failed = True

        self.assertFalse(get_status_failed)

    def test_get_status_no_args(self):
        status_json = json.dumps({StatusMixin.ROOT_STATUS_KEY: StatusMixin.STATUS_OK,
                                  'foo': StatusMixin.STATUS_FAILED})
        self.instance.status = status_json

        ret = self.instance.get_status()

        self.assertEqual(StatusMixin.STATUS_OK, ret)
