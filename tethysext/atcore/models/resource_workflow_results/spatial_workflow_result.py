"""
********************************************************************************
* Name: spatial_workflow_result
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import copy
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult


__all__ = ['SpatialWorkflowResult']


class SpatialWorkflowResult(ResourceWorkflowResult):
    """
    Data model for storing spatial information about resource workflow results.
    """
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.results_views.map_workflow_results_view.MapWorkflowResultsView'  # noqa: E501
    TYPE = 'spatial_workflow_result'

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, geoserver_name, map_manager, spatial_manager, map_renderer='tethys_map_view', *args, **kwargs):
        """
        Constructor.

        Args:
            geoserver_name(str): Name of geoserver setting to use.
            map_manager(MapManager): Instance of MapManager to use for the map view.
            spatial_manager(SpatialManager): Instance of SpatialManager to use for the map view.
        """
        super().__init__(*args, **kwargs)
        self.controller.kwargs = {
            'geoserver_name': geoserver_name,
            '_MapManager': map_manager,
            'map_type': map_renderer,
            '_SpatialManager': spatial_manager
        }

    @property
    def default_options(self):
        """
        Returns default options dictionary for the object.
        """
        default_options = super().default_options
        default_options.update({
            'layer_group_title': 'Results',
            'layer_group_control': 'checkbox'
        })
        return default_options

    @property
    def layers(self):
        if 'layers' not in self.data:
            self.data['layers'] = []
        return copy.deepcopy(self.data['layers'])

    @layers.setter
    def layers(self, value):
        data = copy.deepcopy(self.data)
        data['layers'] = value
        self.data = data

    def get_layer(self, layer_id):
        """
        Get layer with given identifier. If layer has layer_id attribute it will be checked, otherwise the layer_name attribute will be checked.

        Args:
            layer_id: Identifier of layer (either layer_name or layer_id).

        Returns:
            dict: Layer dictionary.
        """  # noqa: E501
        for layer in self.layers:
            if 'layer_id' in layer and layer['layer_id']:
                if layer_id == layer['layer_id']:
                    return layer

            elif 'layer_name' in layer and layer['layer_name']:
                if layer['layer_name'] == layer_id:
                    return layer
        return None

    def _add_layer(self, layer):
        """
        Add layer to this result.

        Args:
            layer(dict): dictionary containing kwargs for the build layer methods of MapManager.
        """
        layers = self.layers
        layers.append(layer)
        self.layers = layers

    def reset(self):
        self.layers = []

    def add_geojson_layer(self, geojson, layer_name, layer_title, layer_variable, layer_id='', visible=True,
                          public=True, selectable=False, plottable=False, has_action=False, extent=None,
                          popup_title=None, excluded_properties=None, show_download=False, label_options=None):
        """
        Add a geojson layer to display on the map of this result view.

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
            show_download(boolean): enable download layer to shapefile.
            label_options(dict): Dictionary for labeling.  Possibilities include label_property (the name of the
                property to label), font (label font), text_align (alignment of the label), offset_x (x offset). Optional.
        """  # noqa: E501
        layer = {
            'type': 'geojson',
            'geojson': geojson,
            'layer_name': layer_name,
            'layer_title': layer_title,
            'layer_variable': layer_variable,
            'layer_id': layer_id,
            'visible': visible,
            'public': public,
            'selectable': selectable,
            'plottable': plottable,
            'has_action': has_action,
            'extent': extent,
            'popup_title': popup_title,
            'excluded_properties': excluded_properties,
            'show_download': show_download,
            'label_options': label_options,
        }
        self._add_layer(layer)

    def add_wms_layer(self, endpoint, layer_name, layer_title, layer_variable, layer_id='', viewparams=None, env=None,
                      visible=True, public=True, tiled=True, selectable=False, plottable=False, has_action=False,
                      extent=None, popup_title=None, excluded_properties=None, geometry_attribute='geometry',
                      color_ramp_division_kwargs=None, times=None):
        """
        Add a wms layer to display on the map of this result view.

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
            color_ramp_division_kwargs(dict): arguments from map_manager.generate_custom_color_ramp_divisions
            times (list): List of time steps if layer is time-enabled. Times should be represented as strings in ISO 8601 format (e.g.: ["20210322T112511Z", "20210322T122511Z", "20210322T132511Z"]). Currently only supported in CesiumMapView.
        """  # noqa: E501
        layer = {
            'type': 'wms',
            'endpoint': endpoint,
            'layer_name': layer_name,
            'layer_title': layer_title,
            'layer_variable': layer_variable,
            'viewparams': viewparams,
            'env': env,
            'color_ramp_division_kwargs': color_ramp_division_kwargs,
            'layer_id': layer_id,
            'visible': visible,
            'tiled': tiled,
            'public': public,
            'geometry_attribute': geometry_attribute,
            'selectable': selectable,
            'plottable': plottable,
            'has_action': has_action,
            'extent': extent,
            'popup_title': popup_title,
            'excluded_properties': excluded_properties,
            'times': times,
        }

        self._add_layer(layer)

    def add_cesium_layer(self, cesium_type, cesium_json, layer_name, layer_title, layer_variable, layer_id='',
                         visible=True, public=True, selectable=False, plottable=False, has_action=False, extent=None,
                         popup_title=None, excluded_properties=None, show_download=False):
        """
        Add a geojson layer to display on the map of this result view.

        Args:
            cesium_type(enum): 'CesiumModel' or 'CesiumPrimitive'
            cesium_json(dict): Cesium object in json.
            layer_name(str): Name of cesium layer (e.g.: agwa:3a84ff62-aaaa-bbbb-cccc-1a2b3c4d5a6b7c8d-model_boundaries).
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
            show_download(boolean): enable download layer to shapefile.
        """  # noqa: E501
        layer = {
            'cesium_type': cesium_type,
            'cesium_json': cesium_json,
            'layer_name': layer_name,
            'layer_title': layer_title,
            'layer_variable': layer_variable,
            'layer_id': layer_id,
            'visible': visible,
            'public': public,
            'selectable': selectable,
            'plottable': plottable,
            'has_action': has_action,
            'extent': extent,
            'popup_title': popup_title,
            'excluded_properties': excluded_properties,
            'show_download': show_download,
        }
        self._add_layer(layer)

    def update_layer(self, update_layer):
        """
        Update color ramp for layer.

        Args:
            update_layer: layer to update.
        """  # noqa: E501\
        new_data = list()

        for layer in self.layers:
            if_match_layer_id = update_layer['layer_id'] and update_layer['layer_id'] == layer['layer_id']
            if_match_layer_name = update_layer['layer_name'] and update_layer['layer_name'] == layer['layer_name']
            if if_match_layer_id or if_match_layer_name:
                new_data.append(update_layer)
            else:
                new_data.append(layer)

        self.layers = new_data
