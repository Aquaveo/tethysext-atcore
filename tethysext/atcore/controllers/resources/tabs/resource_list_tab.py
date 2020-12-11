"""
********************************************************************************
* Name: resource_list_tab.py
* Author: gagelarsen
* Created On: December 11, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import tethys_gizmos.gizmo_options.datatable_view as gizmo_datatable_view
from .resource_tab import ResourceTab


class ResourceListTab(ResourceTab):
    """
    A tab for the TabbedResourceDetails view that lists collections and files that are contained in those collections.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Methods:
        get_file_collections (required): Override this method to define a list of FileCollections that are shown in this tab.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/files_tab.html'
    post_load_callback = 'files_tab_loaded'

    js_requirements = ResourceTab.js_requirements + [
        x for x in gizmo_datatable_view.DataTableView.get_vendor_js()
    ] + [
        'atcore/resources/files_tab.js',
    ]
    css_requirements = ResourceTab.css_requirements + [
        x for x in gizmo_datatable_view.DataTableView.get_vendor_js()
    ] + [
        'atcore/resources/files_tab.css'
    ]

    def get_file_collections(self, request, resource, session, *args, **kwargs):
        """
        Get the file_collections

        Returns:
            A list of FileCollection clients.
        """
        return []

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceFilesTab template that is used to generate the tab content.
        """
        collections = self.get_file_collections(request, resource, session)
        files_from_collection = {}
        for collection in collections:
            instance_id = collection.instance.id
            files_from_collection[instance_id] = self._path_hierarchy(collection.path)

        context['collections'] = files_from_collection
        return context