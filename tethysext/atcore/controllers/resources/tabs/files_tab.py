"""
********************************************************************************
* Name: files_tab.py
* Author: gagelarsen
* Created On: December 03, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import json
import mimetypes
import os
import time
import uuid

from django.http import HttpResponse, Http404
import tethys_gizmos.gizmo_options.datatable_view as gizmo_datatable_view
from .resource_tab import ResourceTab


class ResourceFilesTab(ResourceTab):
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

    def _path_hierarchy(self, path: str, root_dir: str = None, parent_slug: str = None) -> dict:
        """
        A function used to create a dictionary representation of a folder structure.

        Args:
            path: The path to recursively map to a dictionary.
            root_dir: The root directory to be trimmed off of the absolute paths.
            parent_slug: The slug for the parent used for hiding and showing files.

        Returns:
            dict: A dictionary defining the folder structure of the provided path.
        """
        if root_dir is None:
            root_dir = os.path.abspath(os.path.join(path, os.pardir))
        # Remove the root directory from the string that will be placed in the structure.
        # These paths will be relative to the path provided.
        hierarchy_path = path.replace(root_dir, '')
        hierarchy = {
            'type': 'folder',
            'name': os.path.basename(path),
            'path': hierarchy_path,
            'parent_path': os.path.abspath(os.path.join(hierarchy_path, os.pardir)).replace(root_dir, ''),
            'parent_slug': parent_slug,
            'slug': '_' + hierarchy_path.replace(os.path.sep, '_').replace('.', '_').replace('-', '_'),
        }

        # Try and get a name from the meta file.
        meta_file = os.path.join(path, '__meta__.json')
        if os.path.isfile(meta_file):
            try:
                with open(meta_file) as mf:
                    meta_json = json.load(mf)
                    if 'display_name' in meta_json:
                        hierarchy['name'] = meta_json['display_name']
            except json.JSONDecodeError:
                pass
            print(hierarchy)

        # Try and access 'children' here. If we can't than this is a file.
        try:
            # Recurse through each of the children if it is a directory.
            hierarchy['children'] = []
            for contents in os.listdir(path):
                child = self._path_hierarchy(os.path.join(path, contents), root_dir, hierarchy['slug'])
                hierarchy['children'].append(child)

            # If it is a directory we need to calculate the most recent modified date of a contained file
            hierarchy['date_modified'] = time.ctime(max(os.path.getmtime(root) for root, _, _ in os.walk(path)))

        # Catch the errors and assume we are dealing with a file instead of a directory
        except OSError:
            hierarchy['type'] = 'file'
            hierarchy['date_modified'] = time.ctime(os.path.getmtime(path))

            # Calculate the file size and convert to the appropriate measurement.
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

    def download_file(self, request, resource, session, *args, **kwargs):
        """
        A function to download a file from a request.
        """
        collection_id = request.GET.get('collection-id', None)
        file_path = request.GET.get('file-path', None)
        collections = self.get_file_collections(request, resource, session)
        for collection in collections:
            if uuid.UUID('{' + collection_id + '}') == collection.instance.id:
                base_file_path = collection.path.replace(collection_id, '')
                full_file_path = base_file_path + file_path
                file_ext = os.path.splitext(full_file_path)[1]
                mimetype = mimetypes.types_map[file_ext] if file_ext in mimetypes.types_map.keys() else 'text/plain'
                if os.path.exists(full_file_path):
                    with open(full_file_path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type=mimetype)
                        response['Content-Disposition'] = 'filename=' + os.path.basename(file_path)
                        return response
        raise Http404('Unable to download file.')
