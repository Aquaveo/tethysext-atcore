"""
********************************************************************************
* Name: map_view.py
* Author: nswain
* Created On: October 15, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import uuid
import requests
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from tethys_sdk.permissions import has_permission, permission_required
from tethys_sdk.gizmos import ToggleSwitch, MVLayer
from tethysext.atcore.controllers.resource_view import ResourceView
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.gizmos import SlideSheet


class MapView(ResourceView):
    """
    Controller for a map view page.
    """
    map_title = ''
    map_subtitle = ''
    template_name = 'atcore/map_view/map_view.html'
    http_method_names = ['get', 'post']

    default_disable_basemap = False
    geoserver_name = ''
    geocode_api_key = '449ce48a52689190cb913b284efea8e9'  # TODO: Set as controller arg
    geocode_endpoint = 'http://api.opencagedata.com/geocode/v1/geojson'
    mutiselect = False
    properties_popup_enabled = True

    _MapManager = None
    _ModelDatabase = ModelDatabase
    _SpatialManager = None

    def get_context(self, request, session, resource, context, model_db, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        from django.conf import settings
        scenario_id = request.GET.get('scenario-id', 1)

        # Load Primary Map View
        resource_id = None

        if resource:
            resource_id = resource.id

        # Get Managers Hook
        model_db, map_manager = self.get_managers(
            request=request,
            resource=resource,
            *args, **kwargs
        )

        # Render the Map
        map_view, model_extent, layer_groups = map_manager.compose_map(
            request=request,
            resource_id=resource_id,
            scenario_id=scenario_id,
            *args, **kwargs
        )

        # Tweak map settings
        map_view.legend = False  # Ensure the built-in legend is not turned on.
        map_view.height = '100%'  # Ensure 100% height
        map_view.width = '100%'  # Ensure 100% width
        map_view.disable_basemap = self.should_disable_basemap(
            request=request,
            model_db=model_db,
            map_manager=map_manager
        )

        map_view.controls = [
            'Rotate',
            'FullScreen',
            {'ZoomToExtent': {
                'projection': 'EPSG:4326',
                'extent': model_extent
            }}
        ]

        map_view.feature_selection = {'multiselect': self.mutiselect, 'sensitivity': 4}

        # Initialize context
        context.update({
            'map_view': map_view,
            'map_extent': model_extent,
            'layer_groups': layer_groups,
            'enable_properties_popup': self.properties_popup_enabled,
            'nav_subtitle': self.map_subtitle,
            'workspace': self._SpatialManager.WORKSPACE,
        })

        if resource:
            context.update({'nav_title': self.map_title or resource.name})
        else:
            context.update({'nav_title': self.map_title})

        open_portal_mode = getattr(settings, 'ENABLE_OPEN_PORTAL', False)
        show_rename = has_permission(request, 'rename_layers')
        show_remove = has_permission(request, 'remove_layers')
        show_public_toggle = has_permission(request, 'toggle_public_layers') and open_portal_mode

        context.update({
            'show_rename': show_rename,
            'show_remove': show_remove,
            'show_public_toggle': show_public_toggle
        })

        if open_portal_mode and show_public_toggle:
            layer_dropdown_toggle = ToggleSwitch(display_text='',
                                                 name='layer-dropdown-toggle',
                                                 on_label='Yes',
                                                 off_label='No',
                                                 on_style='success',
                                                 off_style='danger',
                                                 initial=True,
                                                 size='small',
                                                 classes='layer-dropdown-toggle')
            context.update({'layer_dropdown_toggle': layer_dropdown_toggle})

        # Add plot slide sheet
        plot_slidesheet = SlideSheet(
            id='plot-slide-sheet',
            title='Plot',
            content_template='atcore/map_view/map_plot.html'
        )

        context.update({'plot_slide_sheet': plot_slidesheet})

        return context

    def build_geojson_layer(self, geojson, layer_name, layer_variable, legend_title, popup_title, visible=True,
                            feature_selection=True):
        """
        Utility method for building MVLayer objects a GeoJSON formatted geometry.

        Args:
            geojson(dict): GeoJSON Python equivalent.
            layer_name(str): Name of layer.
            layer_variable(str): Type of layer.
            legend_title(str): Title to show in legend.
            popup_title(str): Title to show in pop-ups.
            visible(bool): Layer is initially visible if True.
            feature_selection(bool): Feature selection is enabled on layer if True.

        Returns:
            MVLayer: the layer object.
        """
        # Bind geojson features to layer via layer name
        for feature in geojson['features']:
            feature['properties']['layer_name'] = layer_name

        # Define default styles for layers
        style_map = self.get_vector_style_map()

        # Define the workflow MVLayer
        workflow_layer = MVLayer(
            source='GeoJSON',
            options=geojson,
            legend_title=legend_title,
            data={
                'layer_name': layer_name,
                'layer_variable': layer_variable,
                'popup_title': popup_title,
                'excluded_properties': ['id', 'type', 'layer_name'],
            },
            layer_options={
                'visible': visible,
                'style_map': style_map
            },
            feature_selection=feature_selection
        )
        return workflow_layer

    def build_geoserver_layer(self, service_url, layer_name, layer_variable, legend_title, popup_title, visible=True,
                              feature_selection=True):
        """
        Utility method for building MVLayer objects for GeoServer sources.

        Args:
            service_url(str): URL of OGC service.
            layer_name(str): Name of layer.
            layer_variable(str): Type of layer.
            legend_title(str): Title to show in legend.
            popup_title(str): Title to show in pop-ups.
            visible(bool): Layer is initially visible if True.
            feature_selection(bool): Feature selection is enabled on layer if True.

        Returns:
            MVLayer: the layer object.
        """
        # Define the workflow MVLayer
        workflow_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': service_url,
                'params': {'LAYERS': layer_name},
                'serverType': 'geoserver'
            },
            legend_title=legend_title,
            data={
                'layer_name': layer_name,
                'layer_variable': layer_variable,
                'popup_title': popup_title,
                'excluded_properties': ['id', 'type', 'layer_name'],
            },
            layer_options={
                'visible': visible,
            },
            feature_selection=feature_selection
        )
        return workflow_layer

    @staticmethod
    def get_vector_style_map():
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

    def get_permissions(self, request, permissions, model_db, *args, **kwargs):
        """
        Hook to modify permissions.

        Args:
            request (HttpRequest): The request.
            permissions (dict): The permissions dictionary with boolean values.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified permisssions dictionary.
        """
        permissions = {
            'can_use_geocode': has_permission(request, 'use_map_geocode'),
            'can_use_plot': has_permission(request, 'use_map_plot')
        }
        return permissions

    def should_disable_basemap(self, request, model_db, map_manager):
        """
        Hook to override disabling the basemap.

        Args:
            request (HttpRequest): The request.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            bool: True to disable the basemap.
        """
        return self.default_disable_basemap

    def get_managers(self, request, resource, *args, **kwargs):
        """
        Hook to get managers. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            resource (Resource): Resource instance or None.

        Returns:
            model_db (ModelDatabase): ModelDatabase instance.
            map_manager (MapManager): Map Manager instance
        """  # noqa: E501
        database_id = None

        if resource:
            database_id = resource.get_attribute('database_id')

        if not database_id:
            raise RuntimeError('A resource with database_id attribute is required: '
                               'Resource - {} Database ID - {}'.format(resource, database_id))

        model_db = self._ModelDatabase(app=self._app, database_id=database_id)
        gs_engine = self._app.get_spatial_dataset_service(self.geoserver_name, as_engine=True)
        spatial_manager = self._SpatialManager(geoserver_engine=gs_engine)
        map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=model_db)

        return model_db, map_manager

    def get_plot_data(self, request, session, resource, *args, **kwargs):
        """
        Load plot from given parameters.

        Args:
            request (HttpRequest): The request.
            session(sqlalchemy.Session): The database session.
            resource(Resource): The resource.

        Returns:
            JsonResponse: title, data, and layout options for the plot.
        """
        # Get Resource
        layer_name = request.POST.get('layer_name', '')
        feature_id = request.POST.get('feature_id', '')
        database_id = resource.get_attribute('database_id') if resource else None

        if not database_id:
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return redirect(self.back_url)

        # Initialize MapManager
        model_db = self._ModelDatabase(app=self._app, database_id=database_id)
        gs_engine = self._app.get_spatial_dataset_service(self.geoserver_name, as_engine=True)
        spatial_manager = self._SpatialManager(geoserver_engine=gs_engine)
        map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=model_db)
        title, data, layout = map_manager.get_plot_for_layer_feature(layer_name, feature_id)

        return JsonResponse({'title': title, 'data': data, 'layout': layout})

    @permission_required('use_map_geocode', raise_exception=True)
    def find_location_by_query(self, request, *args, **kwargs):
        """"
        This controller is used in default geocode feature.

        Args:
            request(HttpRequest): The request.
            resource_id(str): UUID of the resource being mapped.
        """
        query = request.POST.get('q', None)
        extent = request.POST.get('extent', None)

        params = {
            'query': query,
            'key': self.geocode_api_key
        }

        if extent:
            params['bounds'] = extent

        response = requests.get(
            url=self.geocode_endpoint,
            params=params
        )

        if response.status_code != 200:
            json = {'success': False,
                    'error': response.text}
            return JsonResponse(json)

        # Construct friendly name for address select
        r_json = response.json()

        # Construct success json and parse out needed info
        json = {'success': True,
                'results': []}

        for address in r_json['features']:
            point = address['geometry']['coordinates']
            scale = 0.001

            if 'bounds' in address['properties']:
                bounds = address['properties']['bounds']

                minx = float(bounds['southwest']['lng'])
                maxx = float(bounds['northeast']['lng'])
                miny = float(bounds['southwest']['lat'])
                maxy = float(bounds['northeast']['lat'])

                diffx = maxx - minx

                if diffx < scale:
                    minx -= scale
                    miny -= scale
                    maxx += scale
                    maxy += scale

            else:
                minx = point[0] - scale
                maxx = point[0] + scale
                miny = point[1] - scale
                maxy = point[1] + scale

            bbox = [minx, miny, maxx, maxy]

            max_name_length = 40
            display_name = address['properties']['formatted']
            if len(display_name) > max_name_length:
                display_name = display_name[:max_name_length] + '...'

            geocode_id = uuid.uuid4()

            json['results'].append({
                'text': display_name,
                'point': point,
                'bbox': bbox,
                'id': 'geocode-' + str(geocode_id)
            })

        return JsonResponse(json)

    @permission_required('use_map_geocode', raise_exception=True)
    def find_location_by_advanced_query(self, request, *args, **kwargs):
        """"
        This controller called by the advanced geocode search feature.

        Args:
            request(HttpRequest): The request.
            resource_id(str): UUID of the resource being mapped.
        """
        query = request.POST.get('q', None)
        # location = request.POST.get('l', None)

        params = {
            'query': query,
            'key': self.geocode_api_key
        }

        response = requests.get(
            url=self.geocode_endpoint,
            params=params
        )

        if response.status_code != 200:
            json = {'success': False,
                    'error': response.text}
            return JsonResponse(json)

        # Construct friendly name for address select
        r_json = response.json()

        # Construct success json and parse out needed info
        json = {'success': True,
                'results': []}

        for address in r_json['features']:
            point = address['geometry']['coordinates']
            scale = 0.001

            if 'bounds' in address['properties']:
                bounds = address['properties']['bounds']

                minx = float(bounds['southwest']['lng'])
                maxx = float(bounds['northeast']['lng'])
                miny = float(bounds['southwest']['lat'])
                maxy = float(bounds['northeast']['lat'])

                diffx = maxx - minx

                if diffx < scale:
                    minx -= scale
                    miny -= scale
                    maxx += scale
                    maxy += scale

            else:
                minx = point[0] - scale
                maxx = point[0] + scale
                miny = point[1] - scale
                maxy = point[1] + scale

            bbox = [minx, miny, maxx, maxy]

            max_name_length = 40
            display_name = address['properties']['formatted']
            if len(display_name) > max_name_length:
                display_name = display_name[:max_name_length] + '...'

            geocode_id = uuid.uuid4()

            json['results'].append({
                'text': display_name,
                'point': point,
                'bbox': bbox,
                'id': 'geocode-' + str(geocode_id)
            })

        return JsonResponse(json)
