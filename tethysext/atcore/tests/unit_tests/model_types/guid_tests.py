import unittest
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CHAR
from tethysext.atcore.models.types import GUID


class MockDialect:

    def __init__(self, name):
        self.name = name

    def type_descriptor(self, val):
        return val


class GuidTests(unittest.TestCase):

    def setUp(self):
        self.mock_postgres_dialect = MockDialect('postgresql')
        self.mock_non_postgres_dialect = MockDialect('non-postgresql')
        self.guid = GUID()
        self.uuid_value = uuid.uuid4()
        self.non_uuid_value = str(self.uuid_value)

    def tearDown(self):
        pass

    def test_load_dialect_impl_postgresql(self):
        return_val = self.guid.load_dialect_impl(self.mock_postgres_dialect)
        self.assertIsInstance(return_val, UUID)

    def test_load_dialect_impl_non_postgresql(self):
        return_val = self.guid.load_dialect_impl(self.mock_non_postgres_dialect)
        self.assertIsInstance(return_val, CHAR)
        self.assertEqual(32, return_val.length)

    def test_process_bind_param_none(self):
        return_val = self.guid.process_bind_param(None, None)
        self.assertIs(None, return_val)

    def test_process_bind_param_postgresql(self):
        return_val = self.guid.process_bind_param(self.non_uuid_value, self.mock_postgres_dialect)
        self.assertEqual(str(self.non_uuid_value), return_val)

    def test_process_bind_param_non_postgresql_non_uuid(self):
        return_val = self.guid.process_bind_param(self.non_uuid_value, self.mock_non_postgres_dialect)
        self.assertEqual("%.32x" % int(uuid.UUID(self.non_uuid_value)), return_val)

    def test_process_bind_param_non_postgresql_uuid(self):
        return_val = self.guid.process_bind_param(self.uuid_value, self.mock_non_postgres_dialect)
        self.assertEqual("%.32x" % int(self.uuid_value), return_val)

    def test_process_result_value_none(self):
        return_val = self.guid.process_result_value(None, None)
        self.assertIs(None, return_val)

    def test_process_result_value(self):
        return_val = self.guid.process_result_value(self.non_uuid_value, None)
        self.assertEqual(uuid.UUID(self.non_uuid_value), return_val)
