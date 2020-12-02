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
    A class-based view/controller that handles the lazily loaded content of a tab on the TabbedResourceDetails view. It should also handle all AJAX calls and form submissions specific to that tab.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Properties:
        template_name (str): The template that is used to render this view.
        base_template (str): The base template from which the default template extends.
        back_url (str): The URL that will be used for the back button on the view.
        http_method_names (list): List of allowed HTTP methods. Defaults to ['get'].
        css_requirements (list<str>): A list of CSS files to load with the view.
        js_requirements (list<str>): A list of JavaScript files to load with the view.
        modal_templates (list<str>): A list of templates containing modals for the view.
        post_load_callback (str): The name of a JavaScript function to call after the tab has loaded.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/resource_tab.html'
    http_method_names = ['get']
    css_requirements = []
    js_requirements = []
    modal_templates = []
    post_load_callback = ''

    @classmethod
    def get_tabbed_view_context(cls, request, context):
        """
        Hook for ResourceTab specific context that needs to be added to the TabbedResourceDetails view. This is usually used for adding variables that need to be used to build modals, which are loaded when the tabbed view loads.

        Args:
            request(HttpRequest): Django HttpRequest.
            context(dict): context object.

        Returns:
            dict: with additional items to add to the context of the TabbedResourceDetails view.
        """  # noqa: E501
        return {}
