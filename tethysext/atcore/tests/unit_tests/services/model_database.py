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
import sqlalchemy
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.services.model_database_connection import ModelDatabaseConnection


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


class ModelDatabaseTests(unittest.TestCase):

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
        self.md = ModelDatabase(self.mock_app)

    def tearDown(self):
        pass

    def test_create_with_id(self):
        pass

    def test_create_without_id(self):
        pass

    def test_get_name(self):
        md = ModelDatabase(self.mock_app, self.database_id)
        result = md.get_name()
        self.assertEqual('{}_{}'.format('foo', self.database_id), result)

    def test_get_id(self):
        md = ModelDatabase(self.mock_app, self.database_id)
        result = md.get_id()
        self.assertEqual(self.database_id, result)

    @mock.patch('tethysext.atcore.services.model_database.ModelDatabaseConnection')
    def test_get_size(self, mock_mdc):
        mmdc = mock_mdc.return_value
        mmdc.get_engine.return_value = MockEngine(CONN_6)
        md = ModelDatabase(self.mock_app)
        result = md.get_size()
        self.assertEqual(75, result)

    @mock.patch('tethysext.atcore.services.model_database.ModelDatabaseConnection')
    def test_get_size_pretty(self, mock_mdc):
        mmdc = mock_mdc.return_value
        mmdc.get_engine.return_value = MockEngine(CONN_6)
        md = ModelDatabase(self.mock_app)
        result = md.get_size(True)
        self.assertEqual(75, result)

    def test_db_url(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.db_url
        self.assertEqual(md.db_url, result)

    def test_db_url_obj(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.db_url_obj
        self.assertEqual(md.db_url_obj, result)

    def test_model_db_connection(self):
        fake_url = 'postgresql://name:pass@localhost:5435/foo_239407239480712394'
        self.mock_app.get_persistent_store_database = mock.MagicMock(
            return_value=fake_url
        )
        md = ModelDatabase(self.mock_app)
        result = md.model_db_connection
        self.assertIsInstance(result, ModelDatabaseConnection)
        self.assertEqual(fake_url, result.db_url)

    def test_get_engine(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.get_engine()
        self.assertIsInstance(result, sqlalchemy.engine.Engine)
        self.assertEqual(str(md.db_url_obj), str(result.url))
        result.dispose()

    def test_get_session(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.get_session()
        self.assertIsInstance(result, sqlalchemy.orm.session.Session)
        result.close()

    def test_get_session_maker(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.get_session_maker()
        self.assertIsInstance(result, sqlalchemy.orm.session.sessionmaker)

    def test_initialize_no_connections(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[]
        )
        md = ModelDatabase(self.mock_app)
        result = md.initialize()
        self.assertFalse(result)

    def test_initialize_empty_only_connections(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_5]
        )
        md = ModelDatabase(self.mock_app)
        result = md.initialize()
        self.assertFalse(result)

    def test_initialize_fail_create(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1, CONN_2]
        )
        self.mock_app.create_persistent_store = mock.MagicMock(
            return_value=False
        )
        md = ModelDatabase(self.mock_app)
        result = md.initialize()
        self.assertFalse(result)

    def test_initialize_valid_no_declarative_bases(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1, CONN_2]
        )
        self.mock_app.create_persistent_store = mock.MagicMock(
            return_value=True
        )
        md = ModelDatabase(self.mock_app, self.database_id)
        result = md.initialize()
        self.assertEqual(self.database_id, result)

    def test_initialize_valid(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1, CONN_2]
        )
        self.mock_app.create_persistent_store = mock.MagicMock(
            return_value=True
        )
        database_id = '546546513216498465'
        md = ModelDatabase(self.mock_app, database_id)
        result = md.initialize(declarative_bases=(MockDeclarativeBase(),))
        self.assertEqual(database_id, result)

    def test__get_cluster_connection_name_for_new_database_no_connections(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertIsNone(result)

    def test__get_cluster_connection_name_for_new_database_only_empty_connections(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_5]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertIsNone(result)

    def test__get_cluster_connection_name_for_new_database_one_empty_connection(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_2, CONN_5]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertEqual(CONN_2, result)

    def test__get_cluster_connection_name_for_new_database_valid(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1, CONN_2]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertEqual(CONN_2, result)

    def test__get_cluster_connection_name_for_new_database_same_count(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1, CONN_3]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertEqual(CONN_1, result)

    def test__get_cluster_connection_name_for_new_database_same_count_and_size(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_4, CONN_2]
        )
        md = ModelDatabase(self.mock_app)
        result = md._get_cluster_connection_name_for_new_database()
        self.assertEqual(CONN_4, result)

    def test_exists(self):
        self.mock_app.persistent_store_exists = mock.MagicMock(
            return_value=True
        )
        md = ModelDatabase(self.mock_app)
        result = md.exists()
        self.mock_app.persistent_store_exists.assert_called_with(md.database_id)
        self.assertTrue(result)

    def test_list(self):
        databases = ['foo']
        self.mock_app.list_persistent_store_databases = mock.MagicMock(
            return_value=databases
        )
        md = ModelDatabase(self.mock_app)
        result = md.list()
        self.mock_app.list_persistent_store_databases.assert_called()
        self.assertEqual(databases, result)

    def test_generate_id(self):
        self.mock_app.list_persistent_store_connections = mock.MagicMock(
            return_value=[CONN_1]
        )
        md = ModelDatabase(self.mock_app)
        result = md.generate_id()
        self.assertIsNotNone(result)
