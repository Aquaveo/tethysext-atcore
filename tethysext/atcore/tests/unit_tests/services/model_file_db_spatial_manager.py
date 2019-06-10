"""
********************************************************************************
* Name: model_db_spatial_manager.py
* Author: nswain
* Created On: July 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
import unittest

from tethysext.atcore.services.model_file_db_spatial_manager import ModelFileDBSpatialManager
from tethysext.atcore.services.base_spatial_manager import reload_config


class _ModelFileDBSpatialManager(ModelFileDBSpatialManager):

    @reload_config()
    def test_decorator(self, reload_config=True):
        return reload_config

    def get_extent_for_project(self, model_db):
        return [-1, 1, -1, 1]


class ModelFileDBSpatialManagerTests(unittest.TestCase):

    def setUp(self):
        self.geoserver_engine = mock.MagicMock()
        self.mfdbsm = ModelFileDBSpatialManager(self.geoserver_engine)

    def tearDown(self):
        pass

    def test_get_extent_for_project(self):
        self.mfdbsm.get_extent_for_project()

    def test_get_projection_units(self):
        self.mfdbsm.get_projection_units()

    def test_get_projection_string(self):
        self.mfdbsm.get_projection_string()
