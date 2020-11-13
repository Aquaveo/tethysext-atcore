"""
********************************************************************************
* Name: tabbed_resource_details.py
* Author: nswain
* Created On: November 12, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from django.shortcuts import render
from django.http import HttpResponseNotFound
from tethys_sdk.permissions import permission_required

from tethysext.atcore.services.app_users.decorators import active_user_required, resource_controller
from tethysext.atcore.controllers.app_users.resource_details import ResourceDetails
from tethysext.atcore.controllers.resources.tabs import ResourceTab


class TabbedResourceDetails(ResourceDetails):
    """
    Class-based view that builds a tabbed details view for a Resource.

    Required URL Parameters:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Properties:
        template_name:
        css_requirements:
        js_requirements:
        tabs:
    """
    template_name = 'atcore/resources/tabbed_resource_details.html'
    css_requirements = [
        'atcore/css/center.css',
        'atcore/css/flat-modal.css',
        'atcore/app_users/css/app_users.css',
        'atcore/app_users/css/resource_details.css'
    ]
    js_requirements = [
        'atcore/js/enable-tabs.js',
        'atcore/js/enable-tooltips.js',
        'atcore/js/csrf.js',
        'atcore/resources/lazy_load_tabs.js'
    ]
    tabs = None

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request, *args, **kwargs)

    @active_user_required()
    @permission_required('view_resources')
    @resource_controller()
    def _handle_get(self, request, session, resource, back_url, *args, tab_slug='', **kwargs):
        """
        Handle GET requests.
        """
        from django.shortcuts import HttpResponse
        # Reroute tab load requests to ResourceTabs
        if request.GET and request.GET.get('load_tab', None):
            return self._handle_load_tab_request(
                request=request,
                resource=resource,
                tab_slug=request.GET.get('load_tab'),
                *args, **kwargs
            )

        tabs = self.get_tabs(
            request=request,
            resource=resource,
            tab_slug=tab_slug,
            *args, **kwargs
        )

        css_requirements, js_requirements = self.build_static_requirements(tabs=tabs)

        context = {
            'resource': resource,
            'back_url': self.back_url,
            'base_template': self.base_template,
            'tabs': tabs,
            'active_tab': tab_slug,
            'css_requirements': css_requirements,
            'js_requirements': js_requirements
        }

        context = self.get_context(request, context)

        return render(request, self.template_name, context)

    def _handle_load_tab_request(self, request, resource, tab_slug, *args, **kwargs):
        """
        Route to ResourceTab to render the tab.
        Args:
            request (HttpRequest): The request.
            resource (str): Resource instance.
            tab_slug (str): Portion of URL that denotes which tab is active.

        Returns:
            HttpResponse: The tab HTML
        """
        tabs = self.get_tabs(
            request=request,
            resource=resource,
            tab_slug=tab_slug,
            *args, **kwargs
        )

        tab_view = None

        for tab in tabs:
            if tab.get('slug') == tab_slug:
                tab_view = tab.get('view')
                break

        if not tab_view:
            return HttpResponseNotFound('"{}" is not a valid tab.'.format(tab_slug))

        tab_controller = tab_view.as_controller(
            _app=self._app,
            _AppUser=self._AppUser,
            _Organization=self._Organization,
            _Resource=self._Resource,
            _PermissionsManager=self._PermissionsManager,
            _persistent_store_name=self._persistent_store_name,
            base_template=self.base_template
        )

        response = tab_controller(
            request=request,
            resource_id=resource.id,
            tab_slug=tab_slug,
            *args,  **kwargs
        )

        return response

    def build_static_requirements(self, tabs):
        """
        Build the static (css and js) requirement lists.
        Args:
          tabs (iterable): List of ResourceTabViews.
        Returns:
            2-tuple: List of combined CSS requirements, List of combined JS requirements.
        """
        css_requirements = []
        js_requirements = []

        # Add unique requirements from tabs
        for tab in tabs:
            tab_view = tab.get('view')
            for css_requirement in tab_view.css_requirements:
                if css_requirements not in css_requirements:
                    css_requirements.append(css_requirement)

            for js_requirement in tab_view.js_requirements:
                if js_requirement not in js_requirements:
                    js_requirements.append(js_requirement)

        # Add unique requirements from self
        for css_requirement in self.css_requirements:
            if css_requirement not in css_requirements:
                css_requirements.append(css_requirement)

        for js_requirement in self.js_requirements:
            if js_requirement not in js_requirements:
                js_requirements.append(js_requirement)

        return css_requirements, js_requirements

    def get_tabs(self, request, resource, tab_slug, *args, **kwargs):
        """
        Hook to allow for more complex Tab definitions.
        Args:
            request (HttpRequest): The request.
            resource (str): Resource instance.
            tab_slug (str): Portion of URL that denotes which tab is active.

        Returns:
            iterable<dict<tab_slug, tab_title, tab_view>>: List of dictionaries w
        """
        if self.tabs is not None:
            return self. tabs

        tabs = ({'slug': 'tab1', 'title': 'Tab 1', 'view': ResourceTab},
                {'slug': 'tab2', 'title': 'Tab 2', 'view': ResourceTab})
        return tabs

    def get_context(self, request, context, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.
        
        Args:
            request (HttpRequest): The request.
            context (dict): The context dictionary.
        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        return context
