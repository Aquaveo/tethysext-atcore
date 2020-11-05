"""
********************************************************************************
* Name: map_manager
* Author: nswain
* Created On: August 30, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import copy
from abc import ABCMeta, abstractmethod
from tethys_gizmos.gizmo_options import MVView, MVLayer
from tethysext.atcore.services.color_ramps import COLOR_RAMPS
import collections


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

    COLOR_RAMPS = COLOR_RAMPS
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

    _DEFAULT_POPUP_EXCLUDED_PROPERTIES = ['id', 'type', 'layer_name']

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
            request(HttpRequest): A Django request object.

        Returns:
            MapView, 4-list<float>: The MapView and extent objects.
        """

    def get_cesium_token(self):
        """
        Get the cesium token for Cesium Views

        Returns:
            str: The cesium API token
        """
        return ''

    def build_param_string(self, **kwargs):
        """
        Build a VIEWPARAMS or ENV string with given kwargs (e.g.: 'foo:1;bar:baz')

        Args:
            **kwargs: key-value pairs of paramaters.

        Returns:
            str: parameter string.
        """
        if not kwargs:
            return ''

        joined_pairs = []
        for k, v in kwargs.items():
            joined_pairs.append(':'.join([k, str(v)]))

        param_string = ';'.join(joined_pairs)
        return param_string

    def build_geojson_layer(self, geojson, layer_name, layer_title, layer_variable, layer_id='', visible=True,
                            public=True, selectable=False, plottable=False, has_action=False, extent=None,
                            popup_title=None, excluded_properties=None, show_download=False):
        """
        Build an MVLayer object with supplied arguments.
        Args:
            geojson(dict): Python equivalent GeoJSON FeatureCollection.
            layer_name(str): Name of GeoServer layer (e.g.: agwa:3a84ff62-aaaa-bbbb-cccc-1a2b3c4d5a6b7c8d-model_boundaries).
            layer_title(str): Title of MVLayer (e.g.: Model Boundaries).
            layer_variable(str): Variable type of the layer (e.g.: model_boundaries).
            layer_id(UUID, int, str): layer_id for non geoserver layer where layer_name may not be unique.
            visible(bool): Layer is visible when True. Defaults to True.
            public(bool): Layer is publicly accessible when app is running in Open Portal Mode if True. Defaults to True.
            selectable(bool): Enable feature selection. Defaults to False.
            plottable(bool): Enable "Plot" button on pop-up properties. Defaults to False.
            has_action(bool): Enable "Action" button on pop-up properties. Defaults to False.
            extent(list): Extent for the layer. Optional.
            popup_title(str): Title to display on feature popups. Defaults to layer title.
            excluded_properties(list): List of properties to exclude from feature popups.
            show_download(boolean): enable download geojson as shapefile. Default is False.

        Returns:
            MVLayer: the MVLayer object.
        """  # noqa: E501
        # Define default styles for layers
        style_map = self.get_vector_style_map()

        # Bind geometry features to layer via layer name
        for feature in geojson['features']:
            feature['properties']['layer_name'] = layer_name

        mv_layer = self._build_mv_layer(
            layer_source='GeoJSON',
            layer_id=layer_id,
            layer_name=layer_name,
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=geojson,
            extent=extent,
            visible=visible,
            public=public,
            selectable=selectable,
            plottable=plottable,
            has_action=has_action,
            popup_title=popup_title,
            excluded_properties=excluded_properties,
            style_map=style_map,
            show_download=show_download,
        )

        return mv_layer

    def build_wms_layer(self, endpoint, layer_name, layer_title, layer_variable, viewparams=None, env=None,
                        color_ramp=None, visible=True, tiled=True, selectable=False, plottable=False,
                        has_action=False, extent=None, public=True, geometry_attribute='geometry', layer_id='',
                        excluded_properties=None, popup_title=None, minimum=None, maximum=None, num_divisions=10,
                        value_precision=2):
        """
        Build an WMS MVLayer object with supplied arguments.
        Args:
            endpoint(str): URL to GeoServer WMS interface.
            layer_name(str): Name of GeoServer layer (e.g.: agwa:3a84ff62-aaaa-bbbb-cccc-1a2b3c4d5a6b7c8d-model_boundaries).
            layer_title(str): Title of MVLayer (e.g.: Model Boundaries).
            layer_variable(str): Variable type of the layer (e.g.: model_boundaries).
            layer_id(UUID, int, str): layer_id for non geoserver layer where layer_name may not be unique.
            viewparams(str): VIEWPARAMS string.
            env(str): ENV string.
            color_ramp(dict): color_ramp_division generated using color_ramp_divisions function. 
            visible(bool): Layer is visible when True. Defaults to True.
            public(bool): Layer is publicly accessible when app is running in Open Portal Mode if True. Defaults to True.
            tiled(bool): Configure as tiled layer if True. Defaults to True.
            selectable(bool): Enable feature selection. Defaults to False.
            plottable(bool): Enable "Plot" button on pop-up properties. Defaults to False.
            has_action(bool): Enable "Action" button on pop-up properties. Defaults to False.
            extent(list): Extent for the layer. Optional.
            popup_title(str): Title to display on feature popups. Defaults to layer title.
            excluded_properties(list): List of properties to exclude from feature popups.
            geometry_attribute(str): Name of the geometry attribute. Defaults to "geometry".
            minimum(float): minimum threshold for the raster.
            maximum(float): maximum threshold for the raster.
            num_divisions(int): number of division for raster.
            value_precision(int): significant digit or the legend.

        Returns:
            MVLayer: the MVLayer object.
        """  # noqa: E501
        # Build params
        params = {}
        params['LAYERS'] = layer_name

        if tiled:
            params.update({
                'TILED': True,
                'TILESORIGIN': '0.0,0.0'
            })

        if viewparams:
            params['VIEWPARAMS'] = viewparams

        if env:
            params['ENV'] = env

        if color_ramp:
            color_ramp_divisions = self.generate_custom_color_ramp_divisions(min_value=minimum, max_value=maximum,
                                                                             num_divisions=num_divisions,
                                                                             value_precision=value_precision,
                                                                             colors=color_ramp)
            if 'ENV' in params.keys():
                params['ENV'] += self.build_param_string(**color_ramp_divisions)
            else:
                params['ENV'] = self.build_param_string(**color_ramp_divisions)
        # Build options
        options = {
            'url': endpoint,
            'params': params,
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous'
        }

        layer_source = 'TileWMS' if tiled else 'ImageWMS'

        if tiled:
            options['tileGrid'] = self.DEFAULT_TILE_GRID

        mv_layer = self._build_mv_layer(
            layer_id=layer_id,
            layer_name=layer_name,
            layer_source=layer_source,
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=options,
            extent=extent,
            visible=visible,
            public=public,
            selectable=selectable,
            plottable=plottable,
            has_action=has_action,
            popup_title=popup_title,
            excluded_properties=excluded_properties,
            geometry_attribute=geometry_attribute
        )

        return mv_layer

    def build_arc_gis_layer(self, endpoint, layer_name, layer_title, layer_variable, viewparams=None, env=None,
                            visible=True, tiled=True, selectable=False, plottable=False, has_action=False, extent=None,
                            public=True, geometry_attribute='geometry', layer_id='', excluded_properties=None,
                            popup_title=None):
        """
        Build an AcrGIS Map Server MVLayer object with supplied arguments.
        Args:
            endpoint(str): URL to GeoServer WMS interface.
            layer_name(str): Name of GeoServer layer (e.g.: agwa:3a84ff62-aaaa-bbbb-cccc-1a2b3c4d5a6b7c8d-model_boundaries).
            layer_title(str): Title of MVLayer (e.g.: Model Boundaries).
            layer_variable(str): Variable type of the layer (e.g.: model_boundaries).
            layer_id(UUID, int, str): layer_id for non geoserver layer where layer_name may not be unique.
            viewparams(str): VIEWPARAMS string.
            env(str): ENV string.
            visible(bool): Layer is visible when True. Defaults to True.
            public(bool): Layer is publicly accessible when app is running in Open Portal Mode if True. Defaults to True.
            tiled(bool): Configure as tiled layer if True. Defaults to True.
            selectable(bool): Enable feature selection. Defaults to False.
            plottable(bool): Enable "Plot" button on pop-up properties. Defaults to False.
            has_action(bool): Enable "Action" button on pop-up properties. Defaults to False.
            extent(list): Extent for the layer. Optional.
            popup_title(str): Title to display on feature popups. Defaults to layer title.
            excluded_properties(list): List of properties to exclude from feature popups.
            geometry_attribute(str): Name of the geometry attribute. Defaults to "geometry".

        Returns:
            MVLayer: the MVLayer object.
        """  # noqa: E501
        # Build options
        options = {
            'url': endpoint,
            'serverType': 'geoserver',
            'crossOrigin': 'anonymous'
        }

        layer_source = 'TileArcGISRest'

        mv_layer = self._build_mv_layer(
            layer_id=layer_id,
            layer_name=layer_name,
            layer_source=layer_source,
            layer_title=layer_title,
            layer_variable=layer_variable,
            options=options,
            extent=extent,
            visible=visible,
            public=public,
            selectable=selectable,
            plottable=plottable,
            has_action=has_action,
            popup_title=popup_title,
            excluded_properties=excluded_properties,
            geometry_attribute=geometry_attribute
        )

        return mv_layer

    def _build_mv_layer(self, layer_source, layer_name, layer_title, layer_variable, options, layer_id=None,
                        extent=None, visible=True, public=True, selectable=False, plottable=False, has_action=False,
                        excluded_properties=None, popup_title=None, geometry_attribute=None, style_map=None,
                        show_download=False):
        """
        Build an MVLayer object with supplied arguments.
        Args:
            layer_source(str): OpenLayers Source to use for the MVLayer (e.g.: "TileWMS", "ImageWMS", "GeoJSON").
            layer_name(str): Name of GeoServer layer (e.g.: agwa:3a84ff62-aaaa-bbbb-cccc-1a2b3c4d5a6b7c8d-model_boundaries).
            layer_title(str): Title of MVLayer (e.g.: Model Boundaries).
            layer_variable(str): Variable type of the layer (e.g.: model_boundaries).
            layer_id(UUID, int, str): layer_id for non geoserver layer where layer_name may not be unique.
            visible(bool): Layer is visible when True. Defaults to True.
            selectable(bool): Enable feature selection. Defaults to False.
            plottable(bool): Enable "Plot" button on pop-up properties. Defaults to False.
            has_action(bool): Enable "Action" button on pop-up properties. Defaults to False.
            extent(list): Extent for the layer. Optional.
            popup_title(str): Title to display on feature popups. Defaults to layer title.
            excluded_properties(list): List of properties to exclude from feature popups.
            geometry_attribute(str): Name of the geometry attribute. Optional.
            style_map(dict): Style map dictionary. See MVLayer documentation for examples of style maps. Optional.
            show_download(boolean): enable download layer. (only works for geojson layer).
        Returns:
            MVLayer: the MVLayer object.
        """  # noqa: E501

        # Derive popup_title if not given
        if not popup_title:
            popup_title = layer_title

        data = {
            'layer_id': str(layer_id) if layer_id else layer_name,
            'layer_name': layer_name,
            'popup_title': popup_title,
            'layer_variable': layer_variable,
            'toggle_status': public,
        }

        # Process excluded properties
        properties_to_exclude = copy.deepcopy(self._DEFAULT_POPUP_EXCLUDED_PROPERTIES)

        if plottable:
            properties_to_exclude.append('plot')

        if excluded_properties and isinstance(excluded_properties, (list, tuple)):
            for ep in excluded_properties:
                if ep not in properties_to_exclude:
                    properties_to_exclude.append(ep)

        data.update({'excluded_properties': properties_to_exclude})

        if plottable:
            data.update({'plottable': plottable})

        if has_action:
            data.update({'has_action': has_action})

        if not extent:
            extent = self.map_extent

        # Build layer options
        layer_options = {"visible": visible, "show_download": show_download}

        if style_map:
            layer_options.update({'style_map': style_map})

        mv_layer = MVLayer(
            source=layer_source,
            options=options,
            layer_options=layer_options,
            legend_title=layer_title,
            legend_extent=extent,
            legend_classes=[],
            data=data,
            feature_selection=selectable
        )

        if geometry_attribute:
            mv_layer.geometry_attribute = geometry_attribute

        return mv_layer

    def build_layer_group(self, id, display_name, layers, layer_control='checkbox', visible=True, public=True):
        """
        Build a layer group object.

        Args:
            id(str): Unique identifier for the layer group.
            display_name(str): Name displayed in MapView layer selector/legend.
            layers(list<MVLayer>): List of layers to include in the layer group.
            layer_control(str): Type of control for layers. Either 'checkbox' or 'radio'. Defaults to checkbox.
            visible(bool): Whether layer group is initially visible. Defaults to True.
            public(bool): enable public to see this layer group if True.
        Returns:
            dict: Layer group definition.
        """
        if layer_control not in ['checkbox', 'radio']:
            raise ValueError('Invalid layer_control. Must be on of "checkbox" or "radio".')

        layer_group = {
            'id': id,
            'display_name': display_name,
            'control': layer_control,
            'layers': layers,
            'visible': visible,
            'toggle_status': public,
        }
        return layer_group

    def get_vector_style_map(self):
        """
        Builds the style map for vector layers.

        Returns:
            dict: the style map.
        """
        color = 'gold'
        style_map = {
            'Point': {'ol.style.Style': {
                'image': {'ol.style.Circle': {
                    'radius': 5,
                    'fill': {'ol.style.Fill': {
                        'color': color,
                    }},
                    'stroke': {'ol.style.Stroke': {
                        'color': color,
                    }}
                }}
            }},
            'LineString': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': color,
                    'width': 2
                }}
            }},
            'Polygon': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': color,
                    'width': 2
                }},
                'fill': {'ol.style.Fill': {
                    'color': 'rgba(255, 215, 0, 0.1)'
                }}
            }},
        }

        return style_map

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

    def build_legend(self, layer):
        legend_key = layer['layer_variable']
        if ":" in legend_key:
            legend_key = legend_key.replace(":", "_")

        legend_info = {
            'legend_id': legend_key,
            'title': layer['layer_title'],
            'divisions': dict()
        }

        divisions = self.generate_custom_color_ramp_divisions(min_value=layer['minimum'], max_value=layer['maximum'],
                                                              colors=layer['color_ramp'])

        for k, v in divisions.items():
            if 'val' in k and k[:11] != 'val_no_data':
                legend_info['divisions'][float(v)] = divisions[k.replace('val', 'color')]
        legend_info['divisions'] = collections.OrderedDict(
            sorted(legend_info['divisions'].items())
        )

        return legend_info

    def generate_custom_color_ramp_divisions(self, min_value, max_value, num_divisions=10, value_precision=2,
                                             first_division=1, top_offset=0, bottom_offset=0, prefix='val', colors=[],
                                             color_prefix='color'):
        """
        Generate custom elevation divisions.

        Args:
            min_value(number): minimum value.
            max_value(number): maximum value.
            num_divisison(int): number of divisions.
            value_precision(int): level of precision for legend values.
            first_division(int): first division number (defaults to 1).
            top_offset(number): offset from top of color ramp (defaults to 0).
            bottom_offset(number): offset from bottom of color ramp (defaults to 0).
            prefix(str): name of division variable prefix (i.e.: 'val' for pattern 'val1').
            colors(list): hexadesimal colors to build color scale (i.e.: ['#FF0000', '#00FF00', '#0000FF']).
            color_prefix(str): name of color variable prefix (i.e.: 'color' for pattern 'color1').

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
            divisions[f'{prefix}{i}'] = f"{(m * i + b):.{value_precision}f}"
            is_color_list = isinstance(colors, list) and len(colors) > 0
            is_color_ramp = isinstance(colors, str) and colors in COLOR_RAMPS.keys()
            if is_color_list:
                divisions[f'{color_prefix}{i}'] = f"{colors[(i - 1) % len(colors)]}"
            elif is_color_ramp:
                divisions[f'{color_prefix}{i}'] = f"{COLOR_RAMPS[colors][(i - 1) % len(colors)]}"
            else:
                # use default color ramp
                divisions[f'{color_prefix}{i}'] = f"{COLOR_RAMPS['Default'][(i - 1) % len(colors)]}"
        return divisions

    def get_plot_for_layer_feature(self, layer_name, feature_id):
        """
        Get plot data for given feature on given layer.

        Args:
            layer_name(str): Name/id of layer.
            feature_id(str): PostGIS Feature ID of feature.

        Returns:
            str, list<dict>, dict: plot title, data series, and layout options, respectively.
        """
        layout = {
            'xaxis': {
                'title': layer_name
            },
            'yaxis': {
                'title': 'Undefined'
            }
        }

        data = [{
            'name': feature_id,
            'mode': 'lines',
            'x': [1, 2, 3, 4],
            'y': [10, 15, 13, 17],
        }]
        return 'Undefined', data, layout
