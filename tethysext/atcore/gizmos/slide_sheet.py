"""
********************************************************************************
* Name: slight_sheet
* Author: nswain
* Created On: May 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethys_sdk.gizmos import TethysGizmoOptions


class SlideSheet(TethysGizmoOptions):
    """
    Spatial reference select input gizmo.
    """
    gizmo_name = 'slide_sheet'

    def __init__(self, id='slide-sheet', content_template='', title='', attributes=None, classes='', **kwargs):
        """
        constructor

        Args:
            id(str): id of slide sheet. Use this to differentiate multiple slide sheets on the same page.
            content_template(str): path to template to use for slide sheet content.
            title(str): title for slide sheet.
        """
        attributes = {} if attributes is None else attributes

        # Initialize parent
        super(SlideSheet, self).__init__(attributes=attributes, classes=classes)

        self.id = id
        self.content_template = content_template
        self.title = title

        # Add remaining kwargs as attributes so they are accessible to the base template
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def get_gizmo_js():
        """
        JavaScript specific to gizmo.
        """
        return ('atcore/gizmos/slide_sheet/slide_sheet.js',)

    @staticmethod
    def get_gizmo_css():
        """
        CSS specific to gizmo .
        """
        return ('atcore/gizmos/slide_sheet/slide_sheet.css',)
