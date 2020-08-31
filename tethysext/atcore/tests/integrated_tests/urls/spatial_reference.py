"""
********************************************************************************
* Name: spatial_reference.py
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethys_sdk.testing import TethysTestCase
from tethysext.atcore.services.spatial_reference import SpatialReferenceService
from tethysext.atcore.urls import spatial_reference
from tethysext.atcore.controllers.rest.spatial_reference import QuerySpatialReference
from tethysext.atcore.tests.mock.url_map_maker import MockUrlMapMaker


class CustomQuerySpatialReference(QuerySpatialReference):
    pass


class CustomSpatialReferenceService(SpatialReferenceService):
    pass


class InvalidController:
    pass


class SpatialReferenceUrlsTests(TethysTestCase):

    def setUp(self):
        self.base_url_path = 'foo/bar'
        self.names = ['atcore_query_spatial_reference']
        self.urls = ['rest/spatial-reference/query']
        self.num_urls = 1

    def tearDown(self):
        pass

    def name_asserts(self, url_maps):
        for url_map in url_maps:
            name = url_map.name
            self.assertIn(name, self.names)

    def url_asserts(self, url_maps, with_base_url=False):
        if with_base_url:
            compare_urls = [self.base_url_path + '/' + u for u in self.urls]
        else:
            compare_urls = self.urls

        for url_map in url_maps:
            url = url_map.url
            self.assertIn(url, compare_urls)

    def controller_asserts(self, url_maps, controller_names, default_controller, custom_controller):
        num_controllers_tested = 0

        for url_map in url_maps:
            if url_map.name in controller_names:
                controller = url_map.controller
                self.assertTrue(callable(controller))
                self.assertNotEqual(default_controller.as_controller().__name__, controller.__name__)
                self.assertEqual(custom_controller.as_controller().__name__, controller.__name__)
                num_controllers_tested += 1

        self.assertEqual(len(controller_names), num_controllers_tested)

    def test_vanilla(self):
        url_maps = spatial_reference.urls(MockUrlMapMaker, None, None)

        self.name_asserts(url_maps)
        self.assertEqual(len(url_maps), self.num_urls)
        self.name_asserts(url_maps)
        self.url_asserts(url_maps)

    def test_base_url_path(self):
        url_maps = spatial_reference.urls(MockUrlMapMaker, None, None, base_url_path=self.base_url_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_startswith_slash(self):
        startswith_path = '/' + self.base_url_path
        url_maps = spatial_reference.urls(MockUrlMapMaker, None, None, base_url_path=startswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_base_url_path_endswith_slash(self):
        endswith_path = self.base_url_path + '/'
        url_maps = spatial_reference.urls(MockUrlMapMaker, None, None, base_url_path=endswith_path)
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)

    def test_custom_query_spatial_reference_controller(self):
        url_maps = spatial_reference.urls(MockUrlMapMaker, None, None, custom_controllers=[CustomQuerySpatialReference])
        self.assertEqual(len(url_maps), self.num_urls)
        self.controller_asserts(url_maps, ['atcore_query_spatial_reference'], QuerySpatialReference,
                                CustomQuerySpatialReference)

    def test_invalid_controller_arg_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, spatial_reference.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=[InvalidController])

    def test_invalid_controller_arg_not_class(self):
        mockapp = object()
        mock_db_name = "foo"
        self.assertRaises(ValueError, spatial_reference.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_controllers=['not-a-class'])

    def test_custom_base_url_path_and_controllers(self):
        mockapp = object()
        mock_db_name = "foo"
        url_maps = spatial_reference.urls(MockUrlMapMaker, mockapp, mock_db_name, base_url_path=self.base_url_path,
                                          custom_controllers=[CustomQuerySpatialReference])
        self.assertEqual(len(url_maps), self.num_urls)
        self.url_asserts(url_maps, with_base_url=True)
        self.controller_asserts(url_maps, ['atcore_query_spatial_reference'], QuerySpatialReference,
                                CustomQuerySpatialReference)

    def test_custom_services(self):
        # NOTE: Don't know how to validate this... for not just test that it doesn't throw an error.
        mockapp = object()
        mock_db_name = "foo"
        spatial_reference.urls(MockUrlMapMaker, mockapp, mock_db_name, custom_services=[CustomSpatialReferenceService])
        self.assertRaises(ValueError, spatial_reference.urls, MockUrlMapMaker, mockapp, mock_db_name,
                          custom_services=['invalid-service'])
