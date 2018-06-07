"""
********************************************************************************
* Name: model_database_connection.py
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from mock import patch
import sqlalchemy
from tethysext.atcore.services.model_database import ModelDatabaseConnection


def mock_make_session():
    return 'session'


def mock_sessionmaker(bind):
    return 'sessionmaker'


def mock_create_engine(db_url):
    return 'engine'


class ModelDatabaseConnectionTests(unittest.TestCase):

    def setUp(self):
        self.db_id = '123456789'
        self.app_namespace = 'foo'
        self.db_url = 'postgresql://name:pass@localhost:5435/{}_{}'.format(self.app_namespace, self.db_id)

    def tearDown(self):
        pass

    def test_get_id_without_namespace(self):
        mdc = ModelDatabaseConnection(self.db_url)
        result = mdc.get_id()
        self.assertEqual('{}_{}'.format(self.app_namespace, self.db_id), result)

    def test_get_id_with_namespace(self):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_id()
        self.assertEqual(self.db_id, result)

    def test_get_name(self):
        mdc = ModelDatabaseConnection(self.db_url)
        result = mdc.get_name()
        self.assertEqual('{}_{}'.format(self.app_namespace, self.db_id), result)

    def test_get_engine(self):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_engine()
        self.assertIsInstance(result, sqlalchemy.engine.Engine)
        self.assertEqual(mdc.db_url_obj, result.url)
        result.dispose()

    def test_get_session_maker(self):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_session_maker()
        self.assertIsInstance(result, sqlalchemy.orm.session.sessionmaker)

    @patch('sqlalchemy.create_engine', return_value=mock_create_engine)
    @patch('sqlalchemy.orm.sessionmaker', return_value=mock_make_session)
    def test_get_session(self, _, __):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_session()
        self.assertIsInstance(result, sqlalchemy.orm.session.Session)
        result.close()
