"""
********************************************************************************
* Name: utilities
* Author: nswain
* Created On: July 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.test import RequestFactory, TestCase as DjangoTestCase
from tethysext.atcore import utilities


class MockGeoServerEngine(object):

    def __init__(self, endpoint, public_endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.public_endpoint = public_endpoint


class UtilitiesTests(DjangoTestCase):

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

    def test_clean_request_get(self):
        request_factory = RequestFactory()
        request = request_factory.get('/foo/bar', data={'method': 'val', 'foo': 'bar'})
        ret = utilities.clean_request(request)
        self.assertNotIn('method', ret.GET)
        self.assertEqual('bar', ret.GET.get('foo'))

    def test_clean_request_post(self):
        request_factory = RequestFactory()
        request = request_factory.post('/foo/bar', data={'method': 'val', 'foo': 'bar'})
        ret = utilities.clean_request(request)
        self.assertNotIn('method', ret.POST)
        self.assertEqual('bar', ret.POST.get('foo'))

    def test_strip_list(self):
        the_list = ['foo', '', 'bar', '', '']
        ret = utilities.strip_list(the_list)
        self.assertListEqual(['foo', '', 'bar'], ret)

    def test_strip_list_one_special(self):
        the_list = ['foo', '', 'bar', '', 'dog']
        ret = utilities.strip_list(the_list, 'dog')
        self.assertListEqual(['foo', '', 'bar', ''], ret)

    def test_strip_list_multi_special(self):
        the_list = ['foo', '', 'bar', '', 'dog', 'cat']
        ret = utilities.strip_list(the_list, 'dog', 'cat', '')
        self.assertListEqual(['foo', '', 'bar'], ret)

    def test_gramatically_correct_join_one_string(self):
        strings = ['foo']
        ret = utilities.grammatically_correct_join(strings)
        self.assertEqual('foo', ret)

    def test_gramatically_correct_join_two_strings(self):
        strings = ['foo', 'bar']
        ret = utilities.grammatically_correct_join(strings)
        self.assertEqual('foo and bar', ret)

    def test_gramatically_correct_join_three_strings(self):
        strings = ['foo', 'bar', 'goo']
        ret = utilities.grammatically_correct_join(strings)
        self.assertEqual('foo, bar and goo', ret)

    def test_gramatically_correct_join_three_strings_custom_conjuction(self):
        strings = ['foo', 'bar', 'goo']
        ret = utilities.grammatically_correct_join(strings, conjunction='or')
        self.assertEqual('foo, bar or goo', ret)

    def test_generate_geoserver_urls(self):
        gs_engine = MockGeoServerEngine(username='admin', password='geoserver', endpoint='', public_endpoint='')

        utilities.generate_geoserver_urls(gs_engine)
