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
from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection


class ModelFileDatabaseConnectionTests(unittest.TestCase):

    def setUp(self):
        self.db_id = '80a78483_2db9_4729_a8fe_55fcbc8cc3ab'
        self.app_namespace = 'test'
        self.root = '/home/ckrewson/tethys/extensions/tethysext-atcore/tethysext/atcore/tests/files/model_file_database'
        self.db_url = os.path.join(self.root, '{}_{}'.format(self.app_namespace, self.db_id))
        self.mdc = ModelFileDatabaseConnection(self.db_url, self.app_namespace)

    def tearDown(self):
        if os.path.isdir(self.db_url):
            shutil.rmtree(self.db_url)
        if os.path.isfile(os.path.join(self.root, 'test.txt')):
            os.remove(os.path.join(self.root, 'test.txt'))
        if os.path.isdir(os.path.join(self.root, 'test_dir')):
            shutil.rmtree(os.path.join(self.root, 'test_dir'))
        os.makedirs(self.db_url)
        open(os.path.join(self.db_url, "test.txt"), "w+").close()

    def test_get_id_without_namespace_with_underscores_in_id(self):
        mdc = ModelFileDatabaseConnection(self.db_url)
        result = mdc.get_id()
        self.assertEqual('{}_{}'.format(self.app_namespace, self.db_id), result)

    def test_get_id_without_namespace_no_underscores_in_id(self):
        db_id = '80a78483-2db9-4729-a8fe-55fcbc8cc3ab'
        db_url = os.path.join(self.root, db_id)
        mdc = ModelFileDatabaseConnection(db_url)
        result = mdc.get_id()
        self.assertEqual(db_id, result)

    def test_get_id_with_namespace(self):
        result = self.mdc.get_id()
        self.assertEqual(self.db_id, result)

    def test_list(self):
        modellist = ['test.txt']
        result = self.mdc.list()
        self.assertEqual(modellist, result)

    def test_delete_file(self):
        self.mdc.delete('test.txt')
        self.assertFalse(os.path.isfile(os.path.join(self.db_url, 'test.txt')))

    def test_delete_dir(self):
        os.mkdir(os.path.join(self.db_url, 'test_dir'))
        self.mdc.delete('test_dir')
        self.assertFalse(os.path.isdir(os.path.join(self.db_url, 'test_dir')))

    def test_delete_fail(self):
        result = self.mdc.delete('test.dir')
        self.assertRaises(OSError)
        self.assertFalse(result)

    def test_add_file(self):
        test_add = os.path.join(self.root, "test.txt")
        open(test_add, "w+").close()
        self.mdc.add(test_add)
        self.assertTrue(os.path.isfile(os.path.join(self.db_url, 'test.txt')))

    def test_add_dir(self):
        test_add = os.path.join(self.root, "test_dir")
        os.mkdir(test_add)
        print(os.path.isdir(test_add))
        self.mdc.add(test_add)
        self.assertTrue(os.path.isdir(os.path.join(self.db_url, 'test_dir')))

    def test_add_fail(self):
        test_add = os.path.join(self.root, "test_dir")
        result = self.mdc.add(test_add)
        self.assertRaises(OSError)
        self.assertFalse(result)

    def test_duplicate_file(self):
        self.mdc.duplicate('test.txt', 'newtest.txt')
        self.assertTrue(os.path.isfile(os.path.join(self.db_url, 'newtest.txt')))

    def test_duplicate_dir(self):
        test_add = os.path.join(self.db_url, "test_dir")
        os.mkdir(test_add)
        self.mdc.duplicate('test_dir', 'newtest_dir')
        self.assertTrue(os.path.isdir(os.path.join(self.db_url, 'newtest_dir')))

    def test_duplicate_fail(self):
        result = self.mdc.duplicate('test_dir', 'newtest_dir')
        self.assertRaises(OSError)
        self.assertFalse(result)

    def test_move_file(self):
        test_src = os.path.join(self.db_url, "test.txt")
        test_dst = os.path.join(self.root, "test.txt")
        result = self.mdc.move(test_src, test_dst)
        self.assertEqual(test_dst, result)
        self.assertTrue(os.path.isfile(test_dst))

    def test_move_dir(self):
        test_src = os.path.join(self.root, "test_dir")
        test_dst = os.path.join(self.db_url, "test_dir")
        os.mkdir(test_src)
        result = self.mdc.move(test_src, test_dst)
        self.assertEqual(test_dst, result)
        self.assertTrue(os.path.isdir(test_dst))

    def test_move_fail(self):
        test_move = os.path.join(self.root, "test_dir")
        result = self.mdc.move(test_move, self.db_url)
        self.assertRaises(OSError)
        self.assertFalse(result)

    def test_bulk_delete(self):
        test_add1 = os.path.join(self.db_url, "test1.txt")
        open(test_add1, "w+").close()
        delete_list = [test_add1]
        self.mdc.bulk_delete(delete_list)
        self.assertFalse(os.path.isfile(os.path.join(self.db_url, 'test1.txt')))

    def test_bulk_add(self):
        test_add = os.path.join(self.root, "test.txt")
        open(test_add, "w+").close()
        add_list = [test_add]
        self.mdc.bulk_add(add_list)
        self.assertTrue(os.path.isfile(os.path.join(self.db_url, 'test.txt')))

    def test_bulk_duplicate(self):
        duplicate_list = [('test.txt', 'newtest.txt')]
        self.mdc.bulk_duplicate(duplicate_list)
        self.assertTrue(os.path.isfile(os.path.join(self.db_url, 'newtest.txt')))

    def test_bulk_move(self):
        test_src = os.path.join(self.db_url, "test.txt")
        test_dst = os.path.join(self.root, "test.txt")
        move_list = [(test_src, test_dst)]
        self.mdc.bulk_move(move_list)
        self.assertTrue(os.path.isfile(test_dst))
