"""
********************************************************************************
* Name: resource_details.py
* Author: nswain
* Created On: April 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.shortcuts import render, reverse
# Tethys core
from tethys_sdk.permissions import permission_required
from tethys_apps.utilities import get_active_app
# ATCore
from tethysext.atcore.controllers.app_users.base import AppUsersResourceController
from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller


class ResourceDetails(AppUsersResourceController):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = 'atcore/app_users/resource_details.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    @resource_controller()
    def _handle_get(self, request, session, resource, back_url, *args, **kwargs):
        """
        Handle get requests.
        """
        context = {
            'resource': resource,
            'back_url': self.back_url,
            'base_template': self.base_template
        }

        context = self.get_context(request, context)

        return render(request, self.template_name, context)

    def default_back_url(self, request, *args, **kwargs):
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
        return reverse(back_controller)

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
