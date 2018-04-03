"""
********************************************************************************
* Name: manage_organization_members
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Python core
# Django
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
# Tethys core
from tethys_apps.base.controller import TethysController
from tethys_apps.decorators import permission_required
from tethys_gizmos.gizmo_options import TextInput, ToggleSwitch, SelectInput
# CityWater
# TODO: Move epanet helpers into organization organization/services/methods
from tethysapp.epanet.app import LICENSE_DISPLAY_NAMES
from tethysapp.epanet.lib.storage_helpers import DEFAULT_STORAGE
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services._app_users import update_user_permissions


class ManageOrganizationMembers(TethysController):
    """
    Controller for manage_organization_members page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Members'
    template_name = 'atcore/app_users/manage_organization_members.html'
    http_method_names = ['get', 'post']

    def get_app_user_model(self):
        return AppUser

    def get_organization_model(self):
        return Organization

    def get_resource_model(self):
        return Resource

    def get_sessionmaker(self):
        return NotImplementedError

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_modify_user_requests(request)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_modify_user_requests(request, *args, **kwargs)

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
    @permission_required('modify_organizations')
    def _handle_modify_user_requests(self, request, organization_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        UR_APP_ADMIN = 'app_admin'  # TODO: Handle constants
        make_session = self.get_sessionmaker()

        # Process next
        next_arg = request.GET.get('next', "")

        if next_arg == 'manage-organizations':
            next_controller = 'epanet:manage_organizations'
        else:
            next_controller = 'epanet:manage_users'

        # Defaults
        session = SessionMaker()

        # Lookup existing organization
        organization = session.query(Organization).get(organization_id)
        selected_members = [str(u.id) for u in organization.users]

        # Process form submission
        if request.POST and 'modify-members-submit' in request.POST:
            # Validate the form
            selected_members = request.POST.getlist('members-select')

            # Reset Members
            original_members = set(organization.users)
            organization.users = []

            # Add members and assign permissions again
            for user_id in selected_members:
                user = session.query(AppUser).get(user_id)
                organization.users.append(user)

            # Persist changes
            session.commit()

            # Reset permissions on set of old and new members
            # Members that need to be updated are those in the symmetric difference between the set of original members
            # and the set of updated members
            # See: http://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch16s03.html
            updated_members = set(organization.users)
            removed_and_added_members = original_members ^ updated_members

            for member in removed_and_added_members:
                django_user = member.get_django_user()
                if django_user is None:
                    continue
                update_user_permissions(session, django_user)

            session.close()

            # Redirect
            return redirect(reverse(next_controller))

        # Populate members select box
        app_users = get_user_peers(session, request, include_self=True, cascade=True)
        app_users = sorted(app_users, key=lambda u: u.username)

        members_options = set()
        for app_user in app_users:
            django_user = app_user.get_django_user()
            if django_user is None:
                continue
            members_options.add((
                get_display_name_for_django_user(django_user, append_username=True),
                str(app_user.id)
            ))

        # Sort the project options
        members_select = SelectInput(
            display_text='Members',
            name='members-select',
            multiple=True,
            options=members_options,
            initial=selected_members
        )

        session.close()

        context = {
            'members_select': members_select,
            'user_group_name': organization.name,
            'next_controller': next_controller
        }
        session.close()

        return render(request, 'atcore/app_users/modify_user.html', context)
