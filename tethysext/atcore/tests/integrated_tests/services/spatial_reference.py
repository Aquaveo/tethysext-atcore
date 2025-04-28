"""
********************************************************************************
* Name: spatial_reference.py
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from sqlalchemy.engine import create_engine
from tethysext.atcore.tests import TEST_DB_URL
from tethysext.atcore.services.spatial_reference import SpatialReferenceService


def setUpModule():
    global engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    engine.execute('CREATE EXTENSION IF NOT EXISTS postgis;')


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    engine.dispose()


class SpatialReferenceServiceTests(unittest.TestCase):

    def setUp(self):
        self.srs = SpatialReferenceService(db_engine=engine)
        self.srid = '2232'
        self.srid_text = '2232 NAD83 / Colorado Central (ftUS)'

    def tearDown(self):
        pass

    def test_get_spatial_reference_system_by_id_valid_srid(self):
        val = self.srs.get_spatial_reference_system_by_srid(self.srid)
        self.assertIn('results', val)
        self.assertEqual(1, len(val['results']))
        id = val['results'][0]['id']
        text = val['results'][0]['text']
        self.assertEqual(self.srid, id)
        self.assertEqual(self.srid_text, text)

    def test_get_spatial_reference_system_by_id_empty(self):
        val = self.srs.get_spatial_reference_system_by_srid('')
        self.assertIn('results', val)
        self.assertEqual(1, len(val['results']))
        id = val['results'][0]['id']
        text = val['results'][0]['text']
        self.assertEqual('None', id)
        self.assertEqual('None', text)

    def test_get_spatial_reference_system_by_id_none(self):
        val1 = self.srs.get_spatial_reference_system_by_srid('None')
        self.assertIn('results', val1)
        self.assertEqual(1, len(val1['results']))
        id = val1['results'][0]['id']
        text = val1['results'][0]['text']
        self.assertEqual('None', id)
        self.assertEqual('None', text)

        val2 = self.srs.get_spatial_reference_system_by_srid(None)
        self.assertIn('results', val2)
        self.assertEqual(1, len(val2['results']))
        id = val2['results'][0]['id']
        text = val2['results'][0]['text']
        self.assertEqual('None', id)
        self.assertEqual('None', text)

    def test_get_spatial_reference_system_by_query_string_single_term(self):
        single_word_query = ['Colorado']
        val = self.srs.get_spatial_reference_system_by_query_string(single_word_query)

        self.assertIn('results', val)
        self.assertGreater(len(val['results']), 0)

        srid_found = False

        for v in val['results']:
            id = v['id']

            if id == self.srid:
                srid_found = True

            text = v['text']
            self.assertIn('Colorado', text)

        self.assertTrue(srid_found)

    def test_get_spatial_reference_system_by_query_string_multiple_terms(self):
        multiple_words_query = ['Colorado', 'Central']
        val = self.srs.get_spatial_reference_system_by_query_string(multiple_words_query)

        self.assertIn('results', val)
        self.assertGreater(len(val['results']), 0)

        srid_found = False

        for v in val['results']:
            id = v['id']
            if id == self.srid:
                srid_found = True

            text = v['text']
            self.assertTrue('Colorado' in text or 'Central' in text)

        self.assertTrue(srid_found)

    def test_get_spatial_reference_system_by_query_string_empty_string(self):
        empty_words_query = []
        val = self.srs.get_spatial_reference_system_by_query_string(empty_words_query)

        self.assertIn('results', val)
        self.assertEqual(0, len(val['results']))
