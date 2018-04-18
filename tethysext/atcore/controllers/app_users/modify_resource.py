"""
********************************************************************************
* Name: modify_resource.py
* Author: nswain
* Created On: April 18, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
# Tethys core
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from tethys_apps.base.controller import TethysController
from tethys_sdk.permissions import permission_required, has_permission
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import TextInput, ToggleSwitch, SelectInput
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin
from tethysext.atcore.services.app_users.decorators import active_user_required


class ModifyResource(TethysController, AppUsersControllerMixin):
    """
    Controller for modify_organization page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Add Resource'
    template_name = 'atcore/app_users/modify_resource.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    @active_user_required()
    @permission_required('modify_resources')
    def _handle_modify_user_requests(self, request, organization_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        _Resource = self.get_resource_model()
        make_session = self.get_sessionmaker()

        user_session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, user_session)
        user_session.close()


        return render(request, self.template_name, context)