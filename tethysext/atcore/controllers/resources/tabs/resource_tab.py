"""
********************************************************************************
* Name: resource_tab.py
* Author: nswain
* Created On: November 12, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from tethysext.atcore.controllers.resource_view import ResourceView


class ResourceTab(ResourceView):
    """
    A View that handles the lazily loaded contents of tabs on the TabbedResourceDetails view and AJAX calls specific to the tab.

    Properties:
      template_name:
      base_template:
      css_requirements:
      js_requirements:
      modal_templates:
      post_load_callback:
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/resource_tab.html'
    http_method_names = ['get']
    css_requirements = []
    js_requirements = []
    modal_templates = []
    post_load_callback = []

    @classmethod
    def get_tabbed_view_context(cls, request, context):
        """
        Hook for ResourceTab specific context that needs to be added to the TabbedResourceDetails view.
        Args:
            request(HttpRequest): Django HttpRequest.
            context(dict): context object.

        Returns:
            dict: with additional items to add to the context of the TabbedResourceDetails view.
        """
        return {}
