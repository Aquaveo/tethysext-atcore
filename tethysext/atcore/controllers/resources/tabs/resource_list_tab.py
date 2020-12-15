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
from tethysext.atcore.services.app_users.decorators import active_user_required
from tethysext.atcore.services.paginate import paginate


class ResourceListTab(ResourceTab):
    """
    # TODO: DESCRIBE

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Methods:
        get_resources (required): # TODO: DESCRIBE
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/resource_list_tab.html'
    base_template = None
    post_load_callback = 'resource_list_tab_loaded'

    js_requirements = ResourceTab.js_requirements + [
        'atcore/resources/resource_list_tab.js',
        # TODO: Remove if we don't use this.
    ]
    css_requirements = ResourceTab.css_requirements + [
        'atcore/resources/resource_list_tab.css'
        # TODO: Remove if we don't use this.
    ]

    def get_resources(self, request, resource, session, *args, **kwargs):
        """
        Get a list of resources

        Returns:
            A list of FileCollection clients.
        """
        return []

    @active_user_required()
    def _build_resource_cards(self, request, resources):
        _AppUser = self.get_app_user_model()
        make_session = self.get_sessionmaker()
        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        resource_cards = []
        for resource in resources:
            resource_card = resource.__dict__
            resource_card['debugging'] = resource.attributes
            resource_card['debugging']['id'] = str(resource.id)

            resource_card['action'] = 'launch'
            resource_card['action_title'] = 'View Resource'
            resource_card['action_href'] = ''
            resource_cards.append(resource_card)
        return resource_cards

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceFilesTab template that is used to generate the tab content.
        """
        all_resources = self.get_resources(request, resource, session)

        # Build cards
        resource_cards = self._build_resource_cards(request, all_resources)

        context.update({
            'resource_slug': resource.SLUG,
            'resources': resource_cards,
            'base_template': 'atcore/resources/tabs/resource_list_tab_base.html',
        })
        return context
