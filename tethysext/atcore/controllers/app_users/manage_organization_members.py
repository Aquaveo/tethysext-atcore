"""
********************************************************************************
* Name: manage_organization_members
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
# Tethys core
from tethys_apps.base.controller import TethysController
from tethys_apps.decorators import permission_required
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import SelectInput
# CityWater
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin
from tethysext.atcore.services.app_users.decorators import active_user_required


class ManageOrganizationMembers(TethysController, AppUsersControllerMixin):
    """
    Controller for manage_organization_members page.

    GET: Render form for adding/editing user.
    POST: Handle form submission to add/edit a new user.
    """

    page_title = 'Members'
    template_name = 'atcore/app_users/manage_organization_members.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_manage_member_request(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Route post requests.
        """
        return self._handle_manage_member_request(request, *args, **kwargs)

    @active_user_required()
    @permission_required('modify_organization_members')
    def _handle_manage_member_request(self, request, organization_id, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()

        # Process next
        next_arg = request.GET.get('next', "")
        active_app = get_active_app(request)
        app_namespace = active_app.namespace

        if next_arg == 'manage-organizations':
            next_controller = '{}:app_users_manage_organizations'.format(app_namespace)
        else:
            next_controller = '{}:app_users_manage_users'.format(app_namespace)


        session = make_session()
        request_app_user = _AppUser.get_app_user_from_request(request, session)

        # Defaults
        organization = session.query(_Organization).get(organization_id)
        selected_members = [str(u.id) for u in organization.members]
        members_select_errors = ""
        is_client = organization.consultant and organization.consultant.is_member(request_app_user)

        # Process form submission
        if request.POST and 'modify-members-submit' in request.POST:
            # Validate the form
            selected_members = request.POST.getlist('members-select')

            # Cannot remove self
            valid = True

            no_organization_roles = _AppUser.ROLES.get_no_organization_roles()
            if not request_app_user.is_staff() and request_app_user.role not in no_organization_roles:
                if not is_client and str(request_app_user.id) not in selected_members:
                    valid = False
                    selected_members.append(str(request_app_user.id))
                    members_select_errors = "You cannot remove yourself from this organization."

            if valid:
                # Reset Members
                original_members = set(organization.members)
                organization.members = []

                # Add members and assign custom_permissions again
                for user_id in selected_members:
                    user = session.query(_AppUser).get(user_id)
                    organization.members.append(user)

                # Persist changes
                session.commit()

                # Reset custom_permissions on set of old and new members
                # Members that need to be updated are those in the symmetric difference between the set of original members
                # and the set of updated members
                # See: http://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch16s03.html
                updated_members = set(organization.members)
                removed_and_added_members = original_members ^ updated_members

                # Validate removal
                removed_members = original_members - updated_members

                for member in removed_members:
                    if not member.organizations:
                        organization.members.append(member)
                        messages.warning(request, 'Member "{}" was not removed to prevent from being orphaned.'.format(member.username))

                # Persist changes
                session.commit()

                # Update permissions
                permissions_manager = self.get_permissions_manager()

                for member in removed_and_added_members:
                    member.update_permissions(session, request, permissions_manager)

                session.close()

                # Redirect
                return redirect(reverse(next_controller))

        # Populate members select box
        peers = request_app_user.get_peers(session, request, include_self=True, cascade=True)
        peers = sorted(peers, key=lambda u: u.username)

        members_options = set()
        for p in peers:
            members_options.add((
                p.get_display_name(append_username=True),
                str(p.id)
            ))

        # Sort the project options
        members_select = SelectInput(
            display_text='Members',
            name='members-select',
            multiple=True,
            options=members_options,
            initial=selected_members,
            error=members_select_errors
        )

        session.close()

        context = {
            'members_select': members_select,
            'user_group_name': organization.name,
            'next_controller': next_controller
        }
        session.close()

        return render(request, self.template_name, context)
