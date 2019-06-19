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
from tethys_sdk.gizmos import ToggleSwitch
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
    show_custom_layer = True

    _MapManager = None
    _ModelDatabase = ModelDatabase
    _SpatialManager = None
    layer_tab_name = 'Layers'

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

        # Check if we need to create a blank custom layer group
        create_custom_layer = True
        for layer_group in layer_groups:
            if layer_group['id'] == 'custom_layers':
                create_custom_layer = False
                break

        if create_custom_layer:
            custom_layers = map_manager.build_layer_group(id="custom_layers", display_name="Custom Layer", layers='',
                                                          layer_control='checkbox', visible=True)
            layer_groups.append(custom_layers)

        # Initialize context
        context.update({
            'map_view': map_view,
            'map_extent': model_extent,
            'layer_groups': layer_groups,
            'enable_properties_popup': self.properties_popup_enabled,
            'nav_subtitle': self.map_subtitle,
            'workspace': self._SpatialManager.WORKSPACE,
            'back_url': self.back_url,
            'show_custom_layer': self.show_custom_layer,
            'layer_tab_name': self.layer_tab_name,
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

    def get_permissions(self, request, permissions, model_db, *args, **kwargs):
        """
        Hook to modify permissions.

        Args:
            request (HttpRequest): The request.
            permissions (dict): The permissions dictionary with boolean values.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified permissions dictionary.
        """
        permissions = {
            'can_use_geocode': has_permission(request, 'use_map_geocode'),
            'can_use_plot': has_permission(request, 'use_map_plot')
        }
        return permissions

    def save_custom_layers(self, request, session, resource, *args, **kwargs):
        """
        Persist custom layers added to map by user.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): The database session.
            resource(Resource): The resource.

        Returns:
            JsonResponse: success.
        """
        display_name = request.POST.get('layer_name', '')
        layer_uuid = request.POST.get('uuid', '')
        service_link = request.POST.get('service_link', '')
        service_type = request.POST.get('service_type', 'WMS')
        service_layer_name = request.POST.get('service_layer_name', '')
        # TODO: Should use map_manager._build_mv_layer or at the very least MVLayer
        custom_layer = [{'layer_id': layer_uuid, 'display_name': display_name, 'service_link': service_link,
                         'service_type': service_type, 'service_layer_name': service_layer_name}]
        custom_layers = resource.get_attribute('custom_layers')
        if custom_layers is None:
            custom_layers = []
        custom_layers.extend(custom_layer)
        resource.set_attribute('custom_layers', custom_layers)
        session.commit()
        return JsonResponse({'success': True})

    def remove_custom_layer(self, request, session, resource, *args, **kwargs):
        """
        Remove custom layers removed by user.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): The database session.
            resource(Resource): The resource.

        Returns:
            JsonResponse: success.
        """
        layer_id = request.POST.get('layer_id', '')
        layer_group_type = request.POST.get('layer_group_type', '')
        if layer_group_type == 'custom_layers':
            custom_layers = resource.get_attribute(layer_group_type)
            if custom_layers is not None:
                new_custom_layers = []
                for custom_layer in custom_layers:
                    if custom_layer['layer_id'] != layer_id:
                        new_custom_layers.append(custom_layer)
                resource.set_attribute(layer_group_type, new_custom_layers)
        session.commit()
        return JsonResponse({'success': True})

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
        # Lazy load the model_db and map_manager if not defined
        if not getattr(self, '_model_db', None) or not getattr(self, '_map_manager', None):
            database_id = None

            if resource:
                database_id = resource.get_attribute('database_id')

            if not database_id:
                raise RuntimeError('A resource with database_id attribute is required: '
                                   'Resource - {} Database ID - {}'.format(resource, database_id))

            self._model_db = self._ModelDatabase(app=self._app, database_id=database_id)
            gs_engine = self._app.get_spatial_dataset_service(self.geoserver_name, as_engine=True)
            spatial_manager = self._SpatialManager(geoserver_engine=gs_engine)
            self._map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=self._model_db)

        return self._model_db, self._map_manager

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
