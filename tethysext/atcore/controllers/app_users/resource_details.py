"""
********************************************************************************
* Name: resource_details.py
* Author: nswain
* Created On: April 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.shortcuts import render
from django.http import HttpResponse
# Tethys core
from tethys_sdk.base import TethysController
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersResourceControllerMixin
from tethysext.atcore.services.app_users.decorators import active_user_required


class ResourceDetails(TethysController, AppUsersResourceControllerMixin):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = 'atcore/app_users/resource_details.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'delete']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    def _handle_get(self, request, resource_id, *args, **kwargs):
        """
        Handle get requests.
        """
        back_controller = self._get_back_controller(request)
        resource = self._get_resource(request, resource_id, back_controller)

        # TODO: Move permissions check into decorator
        if isinstance(resource, HttpResponse):
            return resource

        context = {
            'resource': resource,
            'back': back_controller,
            'base_template': self.base_template
        }

        context = self.get_context(request, context)

        return render(request, self.template_name, context)

    def _get_back_controller(self, request):
        """
        Derive the back controller.

        Args:
            request: Django HttpRequest.

        Returns:
            str: name of the controller to return to when hitting back or on error.
        """
        # Process next
        back_arg = request.GET.get('back', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace
        if back_arg == 'manage-organizations':
            back_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            back_controller = '{}:app_users_manage_resources'.format(app_namespace)
        return back_controller

    def get_context(self, request, context):
        """
        Hook for modifying context.

        Args:
            request(HttpRequest): Django HttpRequest.
            context(dict): context object.

        Returns:
            dict: context
        """
        return context
