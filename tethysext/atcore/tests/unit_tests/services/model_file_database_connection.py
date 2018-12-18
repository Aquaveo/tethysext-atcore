"""
********************************************************************************
* Name: model_file_database_connection.py
* Author: ckrewson
* Created On: December 12, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
import os
import shutil
from filelock import FileLock
from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection


class ModelFileDatabaseConnectionTests(unittest.TestCase):

    def setUp(self):
        self.db_id = '80a78483_2db9_4729_a8fe_55fcbc8cc3ab'
        self.app_namespace = 'test'
        self.app_files = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.root = os.path.join(self.app_files, 'files', 'model_file_database')
        self.db_dir = os.path.join(self.root, '{}_{}'.format(self.app_namespace, self.db_id))
        self.mdc = ModelFileDatabaseConnection(self.db_dir, self.app_namespace, 0)

    def tearDown(self):
        if os.path.isdir(self.db_dir):
            shutil.rmtree(self.db_dir)
        if os.path.isfile(os.path.join(self.root, 'test.txt')):
            os.remove(os.path.join(self.root, 'test.txt'))
        if os.path.isdir(os.path.join(self.root, 'test_dir')):
            shutil.rmtree(os.path.join(self.root, 'test_dir'))
        os.makedirs(self.db_dir)
        open(os.path.join(self.db_dir, "test.txt"), "w+").close()

    def test_init_without_namespace_with_underscores_in_id(self):
        mdc = ModelFileDatabaseConnection(self.db_dir)
        result = mdc.get_id()
        self.assertEqual('{}_{}'.format(self.app_namespace, self.db_id), result)

    def test_init_without_namespace_no_underscores_in_id(self):
        db_id = '80a78483-2db9-4729-a8fe-55fcbc8cc3ab'
        db_url = os.path.join(self.root, db_id)
        mdc = ModelFileDatabaseConnection(db_url)
        result = mdc.get_id()
        self.assertEqual(db_id, result)

    def test_init_with_namespace(self):
        result = self.mdc.get_id()
        self.assertEqual(self.db_id, result)

    def test_init_without_dir(self):
        self.assertRaises(ValueError, ModelFileDatabaseConnection, None)

    def test_list(self):
        modellist = ['test.txt']
        result = self.mdc.list()
        self.assertEqual(modellist, result)

    def test_delete_file(self):
        self.mdc.delete('test.txt')
        self.assertFalse(os.path.isfile(os.path.join(self.db_dir, 'test.txt')))

    def test_delete_dir(self):
        os.mkdir(os.path.join(self.db_dir, 'test_dir'))
        self.mdc.delete('test_dir')
        self.assertFalse(os.path.isdir(os.path.join(self.db_dir, 'test_dir')))

    def test_delete_fail(self):
        self.assertRaises(ValueError, self.mdc.delete, 'testerror_dir')

    def test_delete_locked(self):
        lock = FileLock(self.mdc.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.mdc.delete, 'test.txt')

    def test_add_file(self):
        test_add = os.path.join(self.root, "test.txt")
        open(test_add, "w+").close()
        os.remove(os.path.join(self.db_dir, "test.txt"))
        self.mdc.add(test_add)
        self.assertTrue(os.path.isfile(os.path.join(self.db_dir, 'test.txt')))

    def test_add_file_exists(self):
        test_add = os.path.join(self.root, "test.txt")
        open(test_add, "w+").close()
        self.mdc.add(test_add)
        self.assertTrue(os.path.isfile(os.path.join(self.db_dir, 'test.txt')))

    def test_add_dir(self):
        test_add = os.path.join(self.root, "test_dir")
        os.mkdir(test_add)
        self.mdc.add(test_add)
        self.assertTrue(os.path.isdir(os.path.join(self.db_dir, 'test_dir')))

    def test_add_fail(self):
        test_add = os.path.join(self.root, "test_dir")
        self.assertRaises(ValueError, self.mdc.add, test_add)

    def test_add_locked(self):
        test_add = os.path.join(self.root, "test.txt")
        open(test_add, "w+").close()
        lock = FileLock(self.mdc.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.mdc.add, test_add)

    def test_duplicate_file(self):
        res = self.mdc.duplicate('test.txt', 'newtest.txt')
        self.assertTrue(os.path.isfile(os.path.join(self.db_dir, 'newtest.txt')))
        self.assertEqual(res, os.path.join(self.db_dir, 'newtest.txt'))

    def test_duplicate_dir(self):
        test_add = os.path.join(self.db_dir, "test_dir")
        os.mkdir(test_add)
        self.mdc.duplicate('test_dir', 'newtest_dir')
        self.assertTrue(os.path.isdir(os.path.join(self.db_dir, 'newtest_dir')))

    def test_duplicate_fail(self):
        self.assertRaises(ValueError, self.mdc.duplicate, 'test_dir', 'newtest_dir')

    def test_duplicate_locked(self):
        src = os.path.join(self.db_dir, 'test_dir')
        os.mkdir(src)
        lock = FileLock(self.mdc.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.mdc.duplicate, 'test_dir', 'newtest_dir')

    def test_move_file(self):
        test_move_dst = os.path.join(self.db_dir, "test_dst")
        test_file_dst = os.path.join(test_move_dst, 'test.txt')
        os.mkdir(test_move_dst)
        result = self.mdc.move("test.txt", os.path.join('test_dst', 'test.txt'))
        self.assertEqual(test_file_dst, result)
        self.assertTrue(os.path.isfile(test_file_dst))

    def test_move_dir(self):
        test_move_src = os.path.join(self.db_dir, "test_src")
        test_move_dst = os.path.join(self.db_dir, "test_dst")
        os.mkdir(test_move_src)
        os.mkdir(test_move_dst)
        test_dir_dst = os.path.join(test_move_dst, 'test_src')
        result = self.mdc.move("test_src", os.path.join('test_dst', 'test_src'))
        self.assertEqual(test_dir_dst, result)
        self.assertTrue(os.path.isdir(test_dir_dst))

    def test_move_fail(self):
        self.assertRaises(ValueError, self.mdc.move, "test_src", "test_dst")

    def test_move_file_exists(self):
        test_move_dst = os.path.join(self.db_dir, "test_dst")
        test_file_dst = os.path.join(test_move_dst, 'test.txt')
        os.mkdir(test_move_dst)
        open(test_file_dst, "w+").close()
        result = self.mdc.move("test.txt", os.path.join('test_dst', 'test.txt'))
        self.assertEqual(test_file_dst, result)
        self.assertTrue(os.path.isfile(test_file_dst))

    def test_move_locked(self):
        test_src = os.path.join(self.db_dir, "test.txt")
        test_dst = os.path.join(self.root, "test.txt")
        lock = FileLock(self.mdc.lock_path, timeout=1)
        with lock.acquire(timeout=15, poll_intervall=0.5):
            self.assertRaises(TimeoutError, self.mdc.move, test_src, test_dst)

    def test_bulk_delete(self):
        os.mkdir(os.path.join(self.db_dir, 'test_dir'))
        delete_list = ['test.txt', 'test_dir']
        self.mdc.bulk_delete(delete_list)
        self.assertFalse(os.path.isfile(os.path.join(self.db_dir, 'test1.txt')))

    def test_bulk_delete_fail(self):
        delete_list = ['test.txt', 'test_dir']
        self.assertRaises(ValueError, self.mdc.bulk_delete, delete_list)

    def test_bulk_add(self):
        test_exists = os.path.join(self.root, "test.txt")
        test_file = os.path.join(self.root, "test1.txt")
        open(test_file, "w+").close()
        test_dir = os.path.join(self.root, "test_dir")
        os.mkdir(test_dir)
        add_list = [test_exists, test_file, test_dir]
        self.mdc.bulk_add(add_list)
        self.assertTrue(os.path.isfile(os.path.join(self.db_dir, 'test1.txt')))

    def test_bulk_add_fail(self):
        test_dir = os.path.join(self.root, "test_dir")
        add_list = [test_dir]
        self.assertRaises(ValueError, self.mdc.bulk_add, add_list)

    def test_bulk_duplicate(self):
        test_dir = os.path.join(self.db_dir, "test_dir")
        os.mkdir(test_dir)
        duplicate_list = [('test.txt', 'newtest.txt'), ('test_dir', 'newtest_dir')]
        self.mdc.bulk_duplicate(duplicate_list)
        self.assertTrue(os.path.isfile(os.path.join(self.db_dir, 'newtest.txt')))

    def test_bulk_duplicate_fail(self):
        duplicate_list = [('test_dir', 'newtest_dir')]
        self.assertRaises(ValueError, self.mdc.bulk_duplicate, duplicate_list)

    def test_bulk_move(self):
        test_move_dst = os.path.join(self.db_dir, "test_dst")
        test_file_dst = os.path.join(test_move_dst, 'test.txt')
        test_exist_dst = os.path.join(test_move_dst, 'test_ex.txt')
        os.mkdir(test_move_dst)
        open(test_exist_dst, "w+").close()
        test_file_path = os.path.join('test_dst', 'test.txt')
        test_ex_path = os.path.join('test_dst', 'test_ex.txt')
        move_list = [("test.txt", test_file_path), ('', test_ex_path)]
        self.mdc.bulk_move(move_list)
        self.assertTrue(os.path.isfile(test_file_dst))

    def test_bulk_move_fail(self):
        duplicate_list = [('test_dir', 'newtest_dir')]
        self.assertRaises(ValueError, self.mdc.bulk_move, duplicate_list)
