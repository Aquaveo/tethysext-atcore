"""
********************************************************************************
* Name: spatial_reference_select.py
* Author: nswain
* Created On: May 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from tethys_sdk.gizmos import TethysGizmoOptions
from tethys_portal.dependencies import vendor_static_dependencies


class SpatialReferenceSelect(TethysGizmoOptions):
    """
    Spatial reference select input gizmo.
    """
    gizmo_name = 'spatial_reference_select'

    def __init__(self, display_name='Spatial Reference System', name='spatial-ref-select', id='spatial-ref-select',
                 placeholder='', query_delay=1000, min_length=2, initial=None, spatial_reference_service='', error='',
                 **kwargs):
        """
        constructor

        Args:
            display_name(str): label for spatial reference select control. Defaults to Spatial "Reference System".
            name(str): name of the spatial reference select control. Defaults to 'spatial-ref-select'.
            id(str): id for spatial reference select control. No id assigned if not specified.
            placeholder(str): placeholder to display when nothing is selected.
            spatial_reference_service(str): spatial reference service url.
            query_delay(int): miliseconds to wait before issueing query to server.
            min_length(int): minimum length of query string required before issueing query to server.
            initial(tuple or None): initial srid selected: (srid_display, srid_value).
            error(str): error message to display on control.
        """
        # Initialize parent
        super(SpatialReferenceSelect, self).__init__(**kwargs)

        self.display_name = display_name
        self.name = name
        self.id = id
        self.placeholder = placeholder
        self.spatial_reference_service = spatial_reference_service
        self.query_delay = query_delay
        self.min_length = min_length
        self.initial = initial
        self.error = error

    @staticmethod
    def get_vendor_js():
        """
        JavaScript vendor libraries
        """
        return (vendor_static_dependencies["select2"].js_url,)

    @staticmethod
    def get_vendor_css():
        """
        CSS vendor libraries
        """
        return (vendor_static_dependencies["select2"].css_url,)

    @staticmethod
    def get_gizmo_js():
        """
        JavaScript specific to gizmo.
        """
        return ('atcore/gizmos/spatial_reference_select/spatial_reference_select.js',)

    @staticmethod
    def get_gizmo_css():
        """
        CSS specific to gizmo .
        """
        return ('atcore/gizmos/spatial_reference_select/spatial_reference_select.css',)
