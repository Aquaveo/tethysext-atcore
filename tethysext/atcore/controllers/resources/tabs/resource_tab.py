"""
********************************************************************************
* Name: resource_tab.py
* Author: nswain
* Created On: November 12, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO
import mimetypes
import os
from django.http import HttpResponse

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

    def _zip_response(self, files, zip_name):
        """
        Build a download response with the given files zipped in memory.

        Args:
            files: list of (abs_path, arcname) tuples.
            zip_name: name of the zip file offered to the browser.
        """
        in_memory = BytesIO()
        # strict_timestamps=False clamps pre-1980 file mtimes, which the ZIP format cannot store
        with ZipFile(in_memory, 'w', compression=ZIP_DEFLATED, strict_timestamps=False) as zf:
            for abs_path, arcname in files:
                zf.write(abs_path, arcname=arcname)
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
        in_memory.seek(0)
        response.write(in_memory.read())
        return response

    def _single_file_response(self, abs_path, filename):
        """
        Build a download response for a single file on disk.
        """
        file_ext = os.path.splitext(abs_path)[1].lower()
        mimetype = mimetypes.types_map.get(file_ext, 'application/octet-stream')
        with open(abs_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mimetype)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
