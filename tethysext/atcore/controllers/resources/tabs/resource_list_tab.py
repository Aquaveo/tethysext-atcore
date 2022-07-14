"""
********************************************************************************
* Name: resource_list_tab.py
* Author: gagelarsen
* Created On: December 11, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from django.shortcuts import reverse

from .resource_tab import ResourceTab


class ResourceListTab(ResourceTab):
    """
    A tab for the TabbedResourceDetails view that lists resources related to this resource.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Methods:
        get_resources (required): Get a list of resources to be associated with this resource.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/resource_list_tab.html'
    base_template = None

    css_requirements = ResourceTab.css_requirements + [
        'atcore/resources/resource_list_tab.css'
    ]

    def get_resources(self, request, resource, session, *args, **kwargs):
        """
        Get a list of resources

        Returns:
            A list of Resources.
        """
        return []

    def get_href_for_resource(self, app_namespace, resource):
        """
        Hook to allow implementations of ResourceListTab to provide action href.
        Args:
            app_namespace (str): the namespace of the app.
            resource (Resource): the current Resource.

        Returns:
            str: the href for the given resource.
        """
        return reverse(f'{app_namespace}:{resource.SLUG}_resource_details',
                       args=[resource.id])

    def _build_resource_cards(self, resources):
        """
        Build a list of cards for resources for the view to use.

        Args:
            resources: A list of resources to convert into cards for the view.

        Returns:
            A list of Resource cards that can be used by the view.
        """
        resource_cards = []
        for resource in resources:
            resource_card = resource.__dict__
            resource_card['action_href'] = self.get_href_for_resource(self._app.package, resource)
            resource_cards.append(resource_card)
        return resource_cards

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceFilesTab template that is used to generate the tab content.
        """
        all_resources = self.get_resources(request, resource, session)

        # Build cards
        resource_cards = self._build_resource_cards(all_resources)

        context.update({
            'resource_slug': resource.SLUG,
            'resources': resource_cards,
            'base_template': 'atcore/resources/tabs/resource_list_tab_base.html',
        })
        return context
