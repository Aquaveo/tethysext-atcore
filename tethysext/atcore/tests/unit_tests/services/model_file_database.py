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
import os
import shutil
from filelock import FileLock
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection


class ModelFileDatabaseTests(unittest.TestCase):

    def setUp(self):
        self.database_id = '80a78483_2db9_4729_a8fe_55fcbc8cc3ab'
        self.app_files = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.test_dir = os.path.join(self.app_files, 'files', 'model_file_database')
        self.app_namespace = 'foo'
        self.mock_app = TethysAppBase()
        self.mock_app.package = 'test'
        self.test_url = os.path.join(self.test_dir, '{}_{}'.format(self.mock_app.package, self.database_id))
        self.mock_app.get_app_workspace = mock.MagicMock()
        self.mock_app.get_app_workspace.return_value = mock.MagicMock(
            path=self.test_dir
        )
        self.md = ModelFileDatabase(self.mock_app, self.database_id)

    def tearDown(self):
        if os.path.isdir(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_url)

    def test_get_name(self):
        result = self.md.get_name()
        self.assertEqual('{}_{}'.format(self.mock_app.package, self.database_id), result)

    def test_get_id(self):
        result = self.md.get_id()
        self.assertEqual(self.database_id, result)

    def test_model_db_connection(self):
        result = self.md.model_db_connection
        self.assertIsInstance(result, ModelFileDatabaseConnection)
        self.assertEqual(self.test_url, result.db_dir)

    def test_directory(self):
        result = self.md.directory
        self.assertEqual(self.test_url, result)

    def test_database_root(self):
        result = self.md.database_root
        self.assertEqual(self.test_dir, result)

    def test_duplicate(self):
        self.md.duplicate()
        self.assertEqual(2, len(os.listdir(self.test_dir)))

    def test_duplicate_locked(self):
        lock = FileLock(self.md.model_db_connection.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.md.duplicate)

    def test_initialize_fail(self):
        self.mock_app.get_app_workspace.return_value = mock.MagicMock(
            path='not/valid/path'
        )
        result = self.md.initialize()
        self.assertFalse(result)

    def test_initialize_valid(self):
        if os.path.isdir(self.test_url):
            shutil.rmtree(self.test_url)
        result = self.md.initialize()
        self.assertEqual(self.database_id, result)

    def test_exists(self):
        result = self.md.exists()
        self.assertTrue(result)

    def test_list(self):
        modellist = []
        result = self.md.list()
        self.assertEqual(modellist, result)

    def test_list_databases(self):
        modellist = ['{}_{}'.format(self.mock_app.package, self.database_id)]
        result = self.md.list_databases()
        self.assertEqual(modellist, result)

    def test_delete(self):
        self.md.delete()
        self.assertEqual(0, len(os.listdir(self.test_dir)))

    def test_delete_locked(self):
        lock = FileLock(self.md.model_db_connection.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.md.delete)
