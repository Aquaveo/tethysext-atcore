"""
********************************************************************************
* Name: model_database_connection.py
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
import sqlalchemy
from tethysext.atcore.services.model_database_connection import ModelDatabaseConnection


class ModelDatabaseConnectionTests(unittest.TestCase):

    def setUp(self):
        self.db_id = '123_456_789'
        self.app_namespace = 'foo'
        self.db_url = 'postgresql://name:pass@localhost:5435/{}_{}'.format(self.app_namespace, self.db_id)

    def tearDown(self):
        pass

    def test_get_id_without_namespace_with_underscores_in_id(self):
        mdc = ModelDatabaseConnection(self.db_url)
        result = mdc.get_id()
        self.assertEqual(self.db_id, result)

    def test_get_id_without_namespace_no_underscores_in_id(self):
        db_id = '123-456-789'
        db_url = 'postgresql://name:pass@localhost:5435/{}'.format(db_id)
        mdc = ModelDatabaseConnection(db_url)
        result = mdc.get_id()
        self.assertEqual(db_id, result)

    def test_get_id_with_namespace(self):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_id()
        self.assertEqual(self.db_id, result)

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

    def test_get_session(self):
        mdc = ModelDatabaseConnection(self.db_url, self.app_namespace)
        result = mdc.get_session()
        self.assertIsInstance(result, sqlalchemy.orm.session.Session)
        result.close()
