"""
********************************************************************************
* Name: summary_tab.py
* Author: nswain
* Created On: November 12, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from django.shortcuts import render

from .resource_tab import ResourceTab


class ResourceSummaryTab(ResourceTab):
    """
    A tab for the TabbedResourceDetails view that lists key-value pair attributes of the Resource. The attributes can be grouped into multiple sections with titles.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Properties:
        has_preview_image (bool): Whether to load a preview image or not. Defaults to False.
        preview_image_title (str): Title to display above the preview image. Defaults to "Preview".

    Methods:
        get_summary_tab_info (required): Override this method to define the attributes that are shown in this tab.
        get_preview_image_url (optional): Override this method to define the URL for the preview image to use.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/summary_tab.html'
    post_load_callback = 'summary_tab_loaded'
    js_requirements = ResourceTab.js_requirements + [
        'atcore/resources/summary_tab.js'
    ]
    has_preview_image = False
    preview_image_title = 'Preview'

    def get_preview_image_url(self, request, resource, *args, **kwargs):
        """
        Define preview image URL for the summary tab.

        Returns:
            str: the image URL.
        """
        return None

    def get_summary_tab_info(self, request, resource, *args, **kwargs):
        """
        Get the summary tab info

        Return Format
        [
            [
                ('Section 1 Title', {'key1': value}),
                ('Section 2 Title', {'key1': value, 'key2': value}),
            ],
            [
                ('Section 3 Title', {'key1': value}),
            ],
        ]
        """
        return []

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceSummaryTab template that is used to generate the tab content.
        """
        if self.has_preview_image:
            context['has_preview_image'] = self.has_preview_image
            context['preview_image_title'] = self.preview_image_title

        general_summary_tab_info = ('Description', {'Name': resource.name, 'Description': resource.description,
                                                    'Created By': resource.created_by,
                                                    'Date Created': resource.date_created})

        # Add general_summary_tab_info as first item in first columns
        summary_tab_info = self.get_summary_tab_info(request, resource)
        if len(summary_tab_info) == 0:
            summary_tab_info = [[general_summary_tab_info]]
        else:
            summary_tab_info[0].insert(0, general_summary_tab_info)

        # Debug Section
        if request.user.is_staff:
            debug_atts = {x.replace("_", " ").title(): y for x, y in resource.attributes.items() if x != 'files'}
            debug_atts['Locked'] = resource.is_user_locked

            if resource.is_user_locked:
                debug_atts['Locked By'] = 'All Users' if resource.is_locked_for_all_users else resource.user_lock
            else:
                debug_atts['Locked By'] = 'N/A'

            debug_summary_tab_info = ('Debug Info', debug_atts)
            summary_tab_info[-1].append(debug_summary_tab_info)

        context['columns'] = summary_tab_info

        return context

    def load_summary_tab_preview_image(self, request, resource, *args, **kwargs):
        """
        Render the summary tab preview image.

        Returns:
            HttpResponse: rendered template.
        """
        preview_map_url = self.get_preview_image_url(
            request=request,
            resource=resource
        )

        context = {
            'preview_title': self.preview_image_title,
            'preview_map_url': preview_map_url
        }
        return render(request, 'atcore/resources/tabs/summary_preview_image.html', context)
