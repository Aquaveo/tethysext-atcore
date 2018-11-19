"""
********************************************************************************
* Name: utilities
* Author: nswain
* Created On: July 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from tethysext.atcore import utilities


class UtilitiesTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_url_with_port(self):
        url = "http://admin:geoserver@localhost:8181/geoserver/rest"
        result_url = utilities.parse_url(url)
        self.assertEqual('admin', result_url.username)
        self.assertEqual('geoserver', result_url.password)
        self.assertEqual('localhost', result_url.host)
        self.assertEqual('8181', result_url.port)
        self.assertEqual('geoserver/rest', result_url.path)
        self.assertEqual('http://localhost:8181/geoserver/rest', result_url.endpoint)

    def test_parse_url_without_port(self):
        url = "http://admin:geoserver@localhost/geoserver/rest"
        result_url = utilities.parse_url(url)
        self.assertEqual('admin', result_url.username)
        self.assertEqual('geoserver', result_url.password)
        self.assertEqual('localhost', result_url.host)
        self.assertEqual('', result_url.port)
        self.assertEqual('geoserver/rest', result_url.path)
        self.assertEqual('http://localhost/geoserver/rest', result_url.endpoint)

    def test_parse_url_without_invalid_url(self):
        self.assertRaises(ValueError,
                          utilities.parse_url,
                          url='foo')
