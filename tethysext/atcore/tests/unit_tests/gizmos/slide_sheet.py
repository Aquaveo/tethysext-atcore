"""
********************************************************************************
* Name: slide_sheet
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
from tethysext.atcore.gizmos import SlideSheet


class SlideSheetTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_with_no_arguments(self):
        val = SlideSheet()
        self.assertIsInstance(val, dict)
        self.assertEqual('slide-sheet', val['id'])
        self.assertEqual('', val['content_template'])
        self.assertEqual('', val['title'])
        self.assertEqual('slide_sheet', val.gizmo_name)

    def test_init_with_arguments(self):

        id = 'slide-sheet'
        content_template = 'content_template'
        title = 'title'
        random = 'random'

        val = SlideSheet(id, content_template, title, random=random)
        self.assertIsInstance(val, dict)
        self.assertEqual(id, val['id'])
        self.assertEqual(content_template, val['content_template'])
        self.assertEqual(title, val['title'])
        self.assertEqual(random, val['random'])
        self.assertEqual('slide_sheet', val.gizmo_name)

    def test_get_gizmo_js(self):
        self.assertIn('slide_sheet.js', SlideSheet.get_gizmo_js()[0])

    def test_get_gizmo_css(self):
        self.assertIn('slide_sheet.css', SlideSheet.get_gizmo_css()[0])
