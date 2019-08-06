"""
********************************************************************************
* Name: spatial_input_mwv_tests.py
* Author: mlebaron
* Created On: August 6, 2016
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MapWorkflowViewTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
