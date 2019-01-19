"""
********************************************************************************
* Name: model_database
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
import mock
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.services.model_database_base import ModelDatabaseBase


CONN_1 = 'conn_1'  #: Count 5 size 10
CONN_2 = 'conn_2'  #: Count 3 size 15
CONN_3 = 'conn_3'  #: Count 5 size 15
CONN_4 = 'conn_4'  #: Count 3 size 15
CONN_5 = 'conn_5'  #: Unassigned connection
CONN_6 = 'conn_6'  #: Get size connection


class MockDeclarativeBase(object):

    class metadata(object):

        @classmethod
        def create_all(self, engine):
            pass


class FetchOne(object):

    def __init__(self, size):
        self.size = size


class MockResponse(object):

    def __init__(self, count=None, size=None):
        self.count = count
        self.size = size

    def scalar(self):
        return self.size

    def fetchone(self):
        return FetchOne(self.size)

    def close(self):
        pass


class MockEngine(object):

    def __init__(self, connection_name):
        self.connection_name = connection_name

    def dispose(self):
        pass

    def execute(self, query):
        """
        Returns different values for different queries.
        CONN_1 and CONN_2 return different count and size.
        CONN_1 and CONN_3 return the same count, but different sizes.
        CONN_2 and CONN_4 return the same count and size.
        CONN_6 return size in shape expected by get_size method.
        Args:
            query(str): the sql query.

        Returns:
            list<MockResponse> or MockResponse: size or count in appropriate container.
        """
        if 'count' in query:
            if self.connection_name == CONN_1:
                return [MockResponse(count=5)]

            if self.connection_name == CONN_2:
                return [MockResponse(count=3)]

            if self.connection_name == CONN_3:
                return [MockResponse(count=5)]

            if self.connection_name == CONN_4:
                return [MockResponse(count=3)]

        elif 'size' in query:
            if self.connection_name == CONN_1:
                return [MockResponse(size=10)]

            if self.connection_name == CONN_2:
                return [MockResponse(size=15)]

            if self.connection_name == CONN_3:
                return [MockResponse(size=15)]

            if self.connection_name == CONN_4:
                return [MockResponse(size=15)]

            if self.connection_name == CONN_6:
                return MockResponse(size=75)


def mock_get_engine(connection_name, as_url=False):
    # Simulate unassigned connection
    if connection_name == CONN_5:
        return None

    if as_url:
        return 'postgresql://name:pass@localhost:5435/{}_{}'.format('foo', connection_name)

    return MockEngine(connection_name)


class ModelDatabaseBaseTests(unittest.TestCase):

    def setUp(self):
        self.database_id = '546546513216498465'
        self.app_namespace = 'foo'
        self.mock_app = TethysAppBase()
        self.mock_app.get_persistent_store_connection = mock.MagicMock(
            side_effect=mock_get_engine
        )
        self.mock_app.get_persistent_store_database = mock.MagicMock(
            side_effect=mock_get_engine
        )
        self.md = ModelDatabaseBase(self.mock_app)

    def tearDown(self):
        pass

    def test_create_with_id(self):
        pass

    def test_create_without_id(self):
        pass

    def test_get_name(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.get_name()
        self.assertIsNone(result)

    def test_get_id(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.get_id()
        self.assertIsNone(result)

    def test_model_db_connection(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.model_db_connection
        self.assertIsNone(result)

    def test_initialize(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.initialize()
        self.assertIsNone(result)

    def test_pre_initialize(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.pre_initialize()
        self.assertIsNone(result)

    def test_post_initialize(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.post_initialize()
        self.assertIsNone(result)

    def test_exists(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.exists()
        self.assertIsNone(result)

    def test_list(self):
        md = ModelDatabaseBase(self.mock_app)
        result = md.list()
        self.assertIsNone(result)

    def test_generate_id(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabaseBase(self.mock_app)
        result = md.generate_id()
        self.assertIsNotNone(result)
