"""
********************************************************************************
* Name: spatial_reference.py
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
from sqlalchemy import create_engine
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.tests import TEST_DB_URL
from tethysext.atcore.controllers.rest.spatial_reference import QuerySpatialReference


def setUpModule():
    global engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    engine.execute('CREATE EXTENSION IF NOT EXISTS postgis;')


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    engine.dispose()


class MockApp:
    def get_persistent_store_database(self, _):
        return engine


class QuerySpatialReferenceControllerTests(TethysTestCase):

    def setUp(self):
        self.srid = '2232'
        self.query = 'Colorado'
        self.user = UserFactory()
        self.request_factory = RequestFactory()

    def tearDown(self):
        pass

    def test_get_q(self):
        request = self.request_factory.get('/foo/bar/', data={'q': self.query})
        request.user = self.user
        mock_app = MockApp()
        response = QuerySpatialReference.as_controller(_app=mock_app, _persistent_store_name='foo')(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('results', content)
        self.assertGreater(len(content['results']), 0)

        srid_found = False

        for result in content['results']:
            if result['id'] == self.srid:
                srid_found = True

            self.assertIn(self.query, result['text'])

        self.assertTrue(srid_found)

    def test_get_id(self):
        request = self.request_factory.get('/foo/bar/', data={'id': self.srid})
        request.user = self.user
        mock_app = MockApp()
        response = QuerySpatialReference.as_controller(_app=mock_app, _persistent_store_name='foo')(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('results', content)
        self.assertEqual(1, len(content['results']))
        self.assertEqual(self.srid, content['results'][0]['id'])
        self.assertGreater(len(content['results'][0]['text']), 0)

    def test_get_wkt(self):
        request = self.request_factory.get('/foo/bar/', data={'wkt': self.srid})
        request.user = self.user
        mock_app = MockApp()
        response = QuerySpatialReference.as_controller(_app=mock_app, _persistent_store_name='foo')(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('results', content)
        self.assertGreater(len(content['results']), 700)
        self.assertTrue(content['results'].startswith('PROJCS["NAD83 / Colorado Central (ftUS)"'))
        self.assertTrue(content['results'].endswith('AUTHORITY["EPSG","2232"]]'))

    def test_get_wkt_no_srid(self):
        request = self.request_factory.get('/foo/bar/', data={'wkt': 'None'})  # SRID empty
        request.user = self.user
        mock_app = MockApp()
        response = QuerySpatialReference.as_controller(_app=mock_app, _persistent_store_name='foo')(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('results', content)
        self.assertEqual(len(content['results']), 0)

    def test_get_wkt_bad_srid(self):
        request = self.request_factory.get('/foo/bar/', data={'wkt': -987654321})  # Bad SRID
        request.user = self.user
        mock_app = MockApp()
        response = QuerySpatialReference.as_controller(_app=mock_app, _persistent_store_name='foo')(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('results', content)
        self.assertEqual(len(content['results']), 0)

    def test_get_none(self):
        request = self.request_factory.get('/foo/bar/')
        request.user = self.user
        response = QuerySpatialReference.as_controller()(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual('application/json', response.get('content-type'))
        content = json.loads(response.content.decode('utf-8'))
        self.assertIn('error', content)
        self.assertEqual('BadRequest: must pass either "id", "q", or "wkt" parameters.', content['error'])

    def test_get_engine_no_app(self):
        request = self.request_factory.get('/foo/bar/', data={'id': self.srid})
        request.user = self.user
        controller_func = QuerySpatialReference.as_controller()
        self.assertRaises(NotImplementedError, controller_func, request)

    def test_get_engine_no_persistent_store_name(self):
        request = self.request_factory.get('/foo/bar/', data={'id': self.srid})
        request.user = self.user
        controller_func = QuerySpatialReference.as_controller(_app=object())
        self.assertRaises(NotImplementedError, controller_func, request)
