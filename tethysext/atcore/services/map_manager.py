"""
********************************************************************************
* Name: map_manager
* Author: nswain
* Created On: August 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from math import ceil
from abc import ABCMeta, abstractmethod
from tethys_gizmos.gizmo_options import MVView


class MapManagerBase(object):
    """
    Base class for object that orchestrates the map layers and resources.
    """
    __metaclass__ = ABCMeta

    MAX_ZOOM = 28
    MIN_ZOOM = 0
    DEFAULT_ZOOM = 4
    DEFAULT_CENTER = [-98.583, 39.833]

    SEED_ZOOM_START = 11
    SEED_ZOOM_END = 14

    LAYER_SOURCE_TYPE = 'TileWMS'

    DEFAULT_TILE_GRID = {
        'resolutions': [
            156543.03390625,
            78271.516953125,
            39135.7584765625,
            19567.87923828125,
            9783.939619140625,
            4891.9698095703125,
            2445.9849047851562,
            1222.9924523925781,
            611.4962261962891,
            305.74811309814453,
            152.87405654907226,
            76.43702827453613,
            38.218514137268066,
            19.109257068634033,
            9.554628534317017,
            4.777314267158508,
            2.388657133579254,
            1.194328566789627,
            0.5971642833948135,
            0.2985821416974068,
            0.1492910708487034,
            0.0746455354243517,
            0.0373227677121758,
            0.0186613838560879,
            0.009330691928044,
            0.004665345964022,
            0.002332672982011,
            0.0011663364910055,
            0.0005831682455027,
            0.0002915841227514,
            0.0001457920613757
        ],
        'extent': [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
        'origin': [0.0, 0.0],
        'tileSize': [256, 256]
    }

    def __init__(self, spatial_manager, model_db):
        self.spatial_manager = spatial_manager
        self.model_db = model_db
        self._map_extent = None
        self._default_view = None

    @property
    def map_extent(self):
        if not self._map_extent:
            view, extent = self.get_map_extent()
            self._map_extent = extent
        return self._map_extent

    @property
    def default_view(self):
        if not self._default_view:
            view, extent = self.get_map_extent()
            self._default_view = view
        return self._default_view

    @abstractmethod
    def compose_map(self, request, *args, **kwargs):
        """
        Compose the MapView object.
        Args:
            request (HttpRequest): A Django request object.

        Returns:
            MapView, 4-list<float>: The MapView and extent objects.
        """

    def get_wms_endpoint(self):
        """
        Get the public wms endpoint for GeoServer.
        """
        return self.spatial_manager.get_wms_endpoint(public=True)

    def get_map_extent(self):
        """
        Get the default view and extent for the project.

        Returns:
            MVView, 4-list<float>: default view and extent of the project.
        """
        extent = self.spatial_manager.get_extent_for_project(
            model_db=self.model_db
        )

        # Compute center
        center = self.DEFAULT_CENTER
        if extent and len(extent) >= 4:
            center_x = (extent[0] + extent[2]) / 2.0
            center_y = (extent[1] + extent[3]) / 2.0
            center = [center_x, center_y]

        # Construct the default view
        view = MVView(
            projection='EPSG:4326',
            center=center,
            zoom=self.DEFAULT_ZOOM,
            maxZoom=self.MAX_ZOOM,
            minZoom=self.MIN_ZOOM
        )

        return view, extent

    def generate_custom_color_ramp_divisions(self, min_value, max_value, num_divisions, first_division=1,
                                             top_offset=0, bottom_offset=0, prefix='val'):
        """
        Generate custom elevation divisions.

        Args:
            min_value(number): minimum value.
            max_value(number): maximum value.
            num_divisison(int): number of divisions.
            first_division(int): first division number (defaults to 1).
            top_offset(number): offset from top of color ramp (defaults to 0).
            bottom_offset(number): offset from bottom of color ramp (defaults to 0).
            prefix=(str): name of division variable prefix (i.e.: 'val' for pattern 'val1').

        Returns:
            dict<name, value>: custom divisions
        """
        divisions = {}

        # Equation of a Line
        max_div = first_division + num_divisions - 1
        min_div = first_division
        max_val = float(max_value - top_offset)
        min_val = float(min_value + bottom_offset)
        y2_minus_y1 = max_val - min_val
        x2_minus_x1 = max_div - min_div
        m = y2_minus_y1 / x2_minus_x1
        b = max_val - (m * max_div)

        for i in range(min_div, max_div + 1):
            divisions['{}{}'.format(prefix, i)] = ceil(m * i + b)

        return divisions
