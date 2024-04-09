"""
********************************************************************************
* Name: base_resource_view.py
* Author: nswain
* Created On: May 6, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponse
from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin

log = logging.getLogger(f'tethys.{__name__}')


class ResourceView(ResourceViewMixin):
    """
    Base controller for all Resource-based views.
    """
    view_title = ''
    view_subtitle = ''
    template_name = ''
    base_template = 'atcore/base.html'

    @active_user_required()
    @resource_controller()
    def get(self, request, session, resource, back_url, *args, **kwargs):
        """
        Handle GET requests.
        """
        from django.conf import settings

        # Call on get hook
        ret_on_get = self.on_get(request, session, resource, *args, **kwargs)
        if ret_on_get and isinstance(ret_on_get, HttpResponse):
            return ret_on_get

        # Check for GET request alternative methods
        the_method = self.request_to_method(request)

        if the_method is not None:
            return the_method(
                *args,
                request=request,
                session=session,
                resource=resource,
                back_url=back_url,
                **kwargs
            )

        # Initialize context
        context = {}

        # Add named url variables to context
        context.update(self.kwargs)

        # Add base view variables to context
        open_portal_mode = getattr(settings, 'ENABLE_OPEN_PORTAL', False)
        context.update({
            'resource': resource,
            'is_in_debug': settings.DEBUG,
            'nav_subtitle': self.view_subtitle,
            'back_url': self.back_url,
            'open_portal_mode': open_portal_mode,
            'base_template': self.base_template
        })

        if resource:
            context.update({'nav_title': self.view_title or resource.name})
        else:
            context.update({'nav_title': self.view_title})

        # Context hook
        context = self.get_context(
            *args,
            request=request,
            session=session,
            context=context,
            resource=resource,
            **kwargs
        )

        # Default Permissions
        permissions = {}

        # Permissions hook
        permissions = self.get_permissions(
            *args,
            request=request,
            permissions=permissions,
            resource=resource,
            **kwargs
        )

        context.update(permissions)

        return render(request, self.template_name, context)

    @active_user_required()
    @resource_controller()
    def post(self, request, session, resource, back_url, *args, **kwargs):
        """
        Route POST requests.
        """
        the_method = self.request_to_method(request)

        if the_method is None:
            return HttpResponseNotFound()

        return the_method(
            *args,
            request=request,
            session=session,
            resource=resource,
            back_url=back_url,
            **kwargs
        )

    def request_to_method(self, request):
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

    def on_get(self, request, session, resource, *args, **kwargs):
        """
        Hook that is called at the beginning of the get request, before any other controller logic occurs.
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
        Returns:
            None or HttpResponse: If an HttpResponse is returned, render that instead.
        """  # noqa: E501
        return None

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        return context

    def get_permissions(self, request, permissions, resource, *args, **kwargs):
        """
        Hook to modify permissions.

        Args:
            request (HttpRequest): The request.
            permissions (dict): The permissions dictionary with boolean values.
            resource (Resource): the resource for this request.

        Returns:
            dict: modified permisssions dictionary.
        """
        return permissions
