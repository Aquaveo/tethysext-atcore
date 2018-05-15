"""
********************************************************************************
* Name: spatial_reference_select
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from tethysext.atcore.gizmos import SpatialReferenceSelect


class SpatialReferenceSelectTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_with_no_arguments(self):
        val = SpatialReferenceSelect()
        self.assertIsInstance(val, dict)
        self.assertEqual('Spatial Reference System', val['display_name'])
        self.assertEqual('spatial-ref-select', val['name'])
        self.assertEqual('spatial-ref-select', val['id'])
        self.assertEqual('', val['placeholder'])
        self.assertEqual(1000, val['query_delay'])
        self.assertEqual(2, val['min_length'])
        self.assertEqual(None, val['initial'])
        self.assertEqual('', val['spatial_reference_service'])
        self.assertEqual('', val['error'])
        self.assertEqual('spatial_reference_select', val.gizmo_name)

    def test_init_with_arguments(self):
        display_name = 'foo'
        name = 'name'
        id = 'id'
        placeholder = 'placeholder'
        query_delay = 1200
        min_length = 3
        initial = ('initial', '')
        spatial_reference_service = 'spatial_reference_service'
        error = 'error'

        val = SpatialReferenceSelect(display_name=display_name, name=name, id=id, placeholder=placeholder,
                                     query_delay=query_delay, min_length=min_length, initial=initial,
                                     spatial_reference_service=spatial_reference_service, error=error)

        self.assertIsInstance(val, dict)
        self.assertEqual(display_name, val['display_name'])
        self.assertEqual(name, val['name'])
        self.assertEqual(id, val['id'])
        self.assertEqual(placeholder, val['placeholder'])
        self.assertEqual(query_delay, val['query_delay'])
        self.assertEqual(min_length, val['min_length'])
        self.assertEqual(initial, val['initial'])
        self.assertEqual(spatial_reference_service, val['spatial_reference_service'])
        self.assertEqual(error, val['error'])
        self.assertEqual('spatial_reference_select', val.gizmo_name)

    def test_get_vendor_js(self):
        self.assertIn('select2.full.min.js', SpatialReferenceSelect.get_vendor_js()[0])

    def test_get_vendor_css(self):
        self.assertIn('select2.min.css', SpatialReferenceSelect.get_vendor_css()[0])

    def test_get_gizmo_js(self):
        self.assertIn('spatial_reference_select.js', SpatialReferenceSelect.get_gizmo_js()[0])

    def test_get_gizmo_css(self):
        self.assertIn('spatial_reference_select.css', SpatialReferenceSelect.get_gizmo_css()[0])
