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
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.contrib import messages
from tethys_sdk.permissions import has_permission, permission_required
from tethysext.atcore.services.app_users.decorators import active_user_required
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
    geocode_api_key = '449ce48a52689190cb913b284efea8e9'
    geocode_endpoint = 'http://api.opencagedata.com/geocode/v1/geojson'
    mutiselect = False

    _MapManager = None
    _ModelDatabase = ModelDatabase
    _SpatialManager = None

    @active_user_required()
    def get(self, request, resource_id=None, *args, **kwargs):
        """
        Handle GET requests.
        """
        from django.conf import settings

        database_id = None
        if resource_id:
            # Get Resource
            resource = self.get_resource(request, resource_id)

            # TODO: Move permissions check into decorator
            if isinstance(resource, HttpResponse):
                return resource

            database_id = resource.get_attribute('database_id')
            if not database_id:
                messages.error(request, 'An unexpected error occurred. Please try again.')
                return redirect(self.back_url)

        # Get Managers Hook
        model_db, map_manager = self.get_managers(
            request,
            resource_id=resource_id,
            database_id=database_id,
            *args, **kwargs
        )

        # Render the Map
        # TODO: Figure out what to do with the scenario_id. Workflow id?
        map_view, model_extent, layer_groups = map_manager.compose_map(
            request,
            resource_id=resource_id,
            scenario_id=1,
            *args, **kwargs
        )

        # Tweak map settings
        map_view.legend = False  # Ensure the built-in legend is not turned on.
        map_view.height = '100%'  # Ensure 100% height
        map_view.width = '100%'  # Ensure 100% width
        map_view.should_disable_basemap = self.should_disable_basemap(
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
        context = {
            'map_view': map_view,
            'map_extent': model_extent,
            'layer_groups': layer_groups,
            'is_in_debug': settings.DEBUG,
            'map_subtitle': self.map_subtitle,
            'workspace': self._SpatialManager.WORKSPACE,
            'back_url': self.back_url
        }

        if resource_id:
            context.update({'resource': resource})
            context.update({'map_title': self.map_title or resource.name})
        else:
            context.update({'map_title': self.map_title})

        # Context hook
        context = self.get_context(
            request=request,
            context=context,
            resource_id=resource_id,
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

    @active_user_required()
    def post(self, request, resource_id, *args, **kwargs):
        """
        Route POST requests.
        """
        method = request.POST.get('method', None)
        if method == 'find-location-by-query':
            return self.find_location_by_query(request)
        elif method == 'find-location-by-advanced-query':
            return self.find_location_by_advanced_query(request)
        elif method == 'get-plot-data':
            layer_name = request.POST.get('layer_name', '')
            feature_id = request.POST.get('feature_id', '')
            return self.get_plot_data(request, resource_id, layer_name, feature_id)
        else:
            return HttpResponseNotFound()

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

    def get_managers(self, request, resource_id, database_id, *args, **kwargs):
        """
        Hook to get managers. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        model_db = self._ModelDatabase(app=self._app, database_id=database_id)
        gs_engine = self._app.get_spatial_dataset_service(self.geoserver_name, as_engine=True)
        spatial_manager = self._SpatialManager(geoserver_engine=gs_engine)
        map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=model_db)

        return model_db, map_manager

    def get_context(self, request, context, resource_id, model_db, map_manager, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
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

    def get_plot_data(self, request, resource_id, layer_name, feature_id):
        """
        Load plot from given parameters.

        Args:
            request: Django HttpRequest.
            resource_id(str): UUID of the resource being mapped.
            layer_name(str): Name of the layer to which the feature belongs.
            feature_id(str): Feature ID of the feature to plot.

        Returns:
            JsonResponse: title, data, and layout options for the plot.
        """
        # Get Resource
        resource = self.get_resource(request, resource_id)

        # TODO: Move permissions check into decorator
        if isinstance(resource, HttpResponse):
            return resource

        database_id = resource.get_attribute('database_id')
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
    def find_location_by_query(self, request):
        """"
        This controller is used in default geocode feature.
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
    def find_location_by_advanced_query(self, request):
        """"
        This controller called by the advanced geocode search feature.
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
