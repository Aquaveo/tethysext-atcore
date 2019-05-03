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
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.contrib import messages
from tethys_sdk.permissions import has_permission, permission_required
from tethys_sdk.gizmos import ToggleSwitch
from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller
from tethysext.atcore.controllers.app_users.base import AppUsersResourceController
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.gizmos import SlideSheet


class MapView(AppUsersResourceController):
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

    @active_user_required()
    @resource_controller()
    def get(self, request, session, resource, back_url, *args, **kwargs):
        """
        Handle GET requests.
        """
        from django.conf import settings
        scenario_id = request.GET.get('scenario-id', 1)

        # Call on get hook
        ret_on_get = self.on_get(request, session, resource, *args, **kwargs)
        if ret_on_get and isinstance(ret_on_get, HttpResponse):
            return ret_on_get

        # Check for GET request alternative methods
        the_method = self.map_request_to_method(request)

        if the_method is not None:
            return the_method(
                request=request,
                session=session,
                resource=resource,
                back_url=back_url,
                *args, **kwargs
            )

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
        context = {
            'resource': resource,
            'map_view': map_view,
            'map_extent': model_extent,
            'layer_groups': layer_groups,
            'is_in_debug': settings.DEBUG,
            'enable_properties_popup': self.properties_popup_enabled,
            'nav_subtitle': self.map_subtitle,
            'workspace': self._SpatialManager.WORKSPACE,
            'back_url': self.back_url,
            'show_custom_layer': self.show_custom_layer,
        }

        if resource:
            context.update({'nav_title': self.map_title or resource.name})
        else:
            context.update({'nav_title': self.map_title})

        open_portal_mode = getattr(settings, 'ENABLE_OPEN_PORTAL', False)
        show_rename = has_permission(request, 'rename_layers')
        show_remove = has_permission(request, 'remove_layers')
        show_public_toggle = has_permission(request, 'toggle_public_layers') and open_portal_mode

        context.update({'open_portal_mode': open_portal_mode,
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

        # Context hook
        context = self.get_context(
            request=request,
            session=session,
            context=context,
            resource=resource,
            model_db=model_db,
            map_manager=map_manager,
            *args, **kwargs
        )

        # Default Permissions
        permissions = {
            'can_use_geocode': has_permission(request, 'use_map_geocode'),
            'can_use_plot': has_permission(request, 'use_map_plot')
        }

        # Permissions hook
        permissions = self.get_permissions(
            request=request,
            permissions=permissions,
            model_db=model_db,
            map_manager=map_manager,
            *args, **kwargs
        )

        context.update(permissions)

        # Add plot slide sheet
        plot_slidesheet = SlideSheet(
            id='plot-slide-sheet',
            title='Plot',
            content_template='atcore/map_view/map_plot.html'
        )

        context.update({'plot_slide_sheet': plot_slidesheet})
        return render(request, self.template_name, context)

    def map_request_to_method(self, request):
        """
        Derive python method on this class from "method" GET or POST parameter.
        Args:
            request (HttpRequest): The request.

        Returns:
            callable: the method or None if not found.
        """
        if request.method == 'POST':
            method = request.POST.get('method', '')
        elif request.method == 'GET':
            method = request.GET.get('method', '')
        else:
            return None
        python_method = method.replace('-', '_')
        the_method = getattr(self, python_method, None)
        return the_method

    @active_user_required()
    @resource_controller()
    def post(self, request, session, resource, back_url, *args, **kwargs):
        """
        Route POST requests.
        """
        the_method = self.map_request_to_method(request)

        if the_method is None:
            return HttpResponseNotFound()

        return the_method(
            request=request,
            session=session,
            resource=resource,
            back_url=back_url,
            *args, **kwargs
        )

    def save_custom_layers(self, request, session, resource, back_url, *args, **kwargs):
        display_name = request.POST.get('layer_name', '')
        layer_uuid = request.POST.get('uuid', '')
        service_link = request.POST.get('service_link', '')
        service_type = request.POST.get('service_type', 'WMS')
        service_layer_name = request.POST.get('service_layer_name', '')
        custom_layer = [{'layer_id': layer_uuid, 'display_name': display_name, 'service_link': service_link,
                         'service_type': service_type, 'service_layer_name': service_layer_name}]
        custom_layers = resource.get_attribute('custom_layers')
        if custom_layers is None:
            custom_layers = []
        custom_layers.extend(custom_layer)
        resource.set_attribute('custom_layers', custom_layers)
        session.commit()
        return JsonResponse({'success': True})

    def remove_custom_layer(self, request, session, resource, back_url, *args, **kwargs):
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

    def on_get(self, request, session, resource, *args, **kwargs):
        """
        Hook that is called at the beginning of the get request, before any other controller logic occurs.
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
        Returns:
            None or HttpResponse: If an HttpResponse is returned, render that instead.
        """  # noqa: E501

    def get_context(self, request, session, resource, context, model_db, map_manager, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        return context

    def get_permissions(self, request, permissions, model_db, map_manager, *args, **kwargs):
        """
        Hook to modify permissions.

        Args:
            request (HttpRequest): The request.
            permissions (dict): The permissions dictionary with boolean values.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified permisssions dictionary.
        """
        return permissions

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
