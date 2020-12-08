"""
********************************************************************************
* Name: files_tab.py
* Author: gagelarsen
* Created On: December 03, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import errno
import os
import time

from .resource_tab import ResourceTab


class ResourceFilesTab(ResourceTab):
    """
    A tab for the TabbedResourceDetails view that lists key-value pair attributes of the Resource. The attributes can be grouped into multiple sections with titles.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Methods:
        get_file_collections (required): Override this method to define a list of FileCollections that are shown in this tab.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/files_tab.html'
    post_load_callback = 'files_tab_loaded'

    js_requirements = ResourceTab.js_requirements + [
        'atcore/resources/files_tab.js'
    ]
    css_requirements = ResourceTab.css_requirements + [
        'atcore/resources/files_tab.css'
    ]

    def get_file_collections(self, request, resource, *args, **kwargs):
        """
        Get the summary tab info

        Return Format
        [FileCollectionClient, FileCollectionClient, FileCollectionClient]
        """
        return []

    def _path_hierarchy(self, path, root_dir=None, parent_slug=None):
        if root_dir is None:
            root_dir = os.path.abspath(os.path.join(path, os.pardir))
        hierarchy_path = path.replace(root_dir, '')
        hierarchy = {
            'type': 'folder',
            'name': os.path.basename(path),
            'path': hierarchy_path,
            'parent_path': os.path.abspath(os.path.join(hierarchy_path, os.pardir)).replace(root_dir, ''),
            'parent_slug': parent_slug,
            'slug': '_' + hierarchy_path.replace(os.path.sep, '_').replace('.', '_').replace('-', '_'),
        }

        try:
            hierarchy['children'] = [
                self._path_hierarchy(os.path.join(path, contents), root_dir, hierarchy['slug'])
                for contents in os.listdir(path)
            ]
            hierarchy['date_modified'] = time.ctime(max(os.path.getmtime(root) for root, _, _ in os.walk(path)))

        except OSError as e:
            if e.errno != errno.ENOTDIR:
                raise
            hierarchy['type'] = 'file'
            hierarchy['date_modified'] = time.ctime(os.path.getmtime(path))

            power = 2 ** 10
            n = 0
            power_labels = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
            size = os.path.getsize(path)
            while size > power:
                size /= power
                n += 1
            size_str = f'{size:.1f}' if size > 0 else '0'
            hierarchy['size'] = f'{size_str} {power_labels[n]}'

        return hierarchy

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceFilesTab template that is used to generate the tab content.
        """
        collections = self.get_file_collections(request, resource)
        files_from_collection = {}
        for collection in collections:
            instance_id = collection.instance.id
            files_from_collection[instance_id] = self._path_hierarchy(collection.path)

        context['collections'] = files_from_collection
        return context
