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
    css_requirements = []
    js_requirements = []
    modal_templates = []
    post_load_callback = []
