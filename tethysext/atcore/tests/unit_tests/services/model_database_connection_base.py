"""
********************************************************************************
* Name: model_database_connection.py
* Author: nswain
* Created On: June 07, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from tethysext.atcore.services.model_database_connection_base import ModelDatabaseConnectionBase


class ModelDatabaseConnectionBaseTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_name(self):
        mdcb = ModelDatabaseConnectionBase()
        result = mdcb.get_name()
        self.assertIsNone(result)

    def test_get_id(self):
        mdcb = ModelDatabaseConnectionBase()
        result = mdcb.get_id()
        self.assertIsNone(result)
