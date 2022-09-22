"""
********************************************************************************
* Name: resource_tab_tests.py
* Author: nswain
* Created On: November 23, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
from os import environ
from django.test import RequestFactory
from tethys_sdk.testing import TethysTestCase

from tethysext.atcore.controllers.resources import ResourceTab


class ResourceTabTests(TethysTestCase):

    def setUp(self):
        environ['TETHYS_TESTING_IN_PROGRESS'] = 'true'
        logging.disable(logging.WARNING)
        super().setUp()

        self.request_factory = RequestFactory()

    def tearDown(self):
        environ['TETHYS_TESTING_IN_PROGRESS'] = ''
        super().tearDown()

    def test_default_properties(self):
        """Verify the default values for the properties of the view."""
        self.assertEqual('atcore/resources/tabs/resource_tab.html', ResourceTab.template_name)
        self.assertListEqual(['get'], ResourceTab.http_method_names)
        self.assertListEqual([], ResourceTab.css_requirements)
        self.assertListEqual([], ResourceTab.js_requirements)
        self.assertListEqual([], ResourceTab.modal_templates)
        self.assertEqual('', ResourceTab.post_load_callback)

    def test_get_tabbed_view_context(self):
        """Test the default implementation of ResourceTab.get_tabbed_view_context()."""
        request = self.request_factory.get('/foo/')
        context = {'foo': 'bar'}

        ret = ResourceTab.get_tabbed_view_context(request, context)

        self.assertDictEqual({}, ret)
