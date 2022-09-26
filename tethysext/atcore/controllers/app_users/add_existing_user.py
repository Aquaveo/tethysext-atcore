from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from tethys_apps.utilities import get_active_app
from tethys_gizmos.gizmo_options import SelectInput
from tethysext.atcore.services.app_users.func import get_display_name_for_django_user
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin


class AddExistingUser(AppUsersViewMixin):
    """
    Controller for add_existing_user page.

    GET: Render form for adding an existing user from the Django user database.
    POST: Handle form submission to add an existing a new user from the Django user database.
    """
    page_title = 'Add Existing User'
    template_name = 'atcore/app_users/add_existing_user.html'
    base_template = 'atcore/app_users/base.html'
    http_method_names = ['get', 'post']

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

    @method_decorator(staff_member_required)
    def _handle_modify_user_requests(self, request, user_id=None, *args, **kwargs):
        """
        Handle get requests.
        """
        from django.contrib.auth.models import User
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        SessionMaker = self.get_sessionmaker()

        valid = True
        selected_portal_users = []
        selected_portal_users_error = ""
        selected_role = ""
        role_select_error = ""
        selected_organizations = []
        organization_select_error = ""

        session = SessionMaker()
        request_app_user = _AppUser.get_app_user_from_request(request, session)
        organization_options = request_app_user.get_organizations(session, request, as_options=True, cascade=True)
        role_options = request_app_user.get_assignable_roles(request, as_options=True)
        no_organization_roles = _AppUser.ROLES.get_no_organization_roles()
        session.close()

        active_app = get_active_app(request)
        app_namespace = active_app.url_namespace
        next_controller = '{}:app_users_manage_users'.format(app_namespace)

        # Process form request
        if request.POST and 'add-existing-user-submit' in request.POST:
            selected_portal_users = request.POST.getlist('portal-users')
            selected_role = request.POST.get('assign-role', '')
            selected_organizations = request.POST.getlist('assign-organizations', [])

            # Validate
            if not selected_role:
                valid = False
                role_select_error = "A role must be assigned to user."

            if len(selected_portal_users) < 1:
                valid = False
                selected_portal_users_error = "Must select at least one user."

            # Must assign user to at least one organization
            organization_required_roles = _AppUser.ROLES.get_organization_required_roles()
            if selected_role in organization_required_roles and not selected_organizations:
                valid = False
                organization_select_error = "Must assign user to at least one organization"

            # Reset selected organization (if any) when role requires no organization
            if selected_organizations and selected_role in no_organization_roles:
                selected_organizations = []

            if valid:
                # Create a new AppUser for each django user and associate it with the Django users with the username
                create_session = SessionMaker()

                for django_username in selected_portal_users:
                    new_app_user = _AppUser(
                        username=django_username,
                        role=selected_role
                    )

                    # Get custom_permissions manager
                    permissions_manager = self.get_permissions_manager()

                    # django_user = new_app_user.get_django_user()

                    # To be safe we will remove all roles that may
                    # already be applied to the user django user associated with the new app user
                    # to give us a clean slate
                    permissions_manager.remove_all_permissions_groups(new_app_user)

                    # Users cannot change their own role
                    if selected_role and new_app_user.username != request.user.username:
                        new_app_user.role = selected_role

                    # Add user to selected organizations and assign custom_permissions
                    if selected_role not in no_organization_roles:
                        for organization_id in selected_organizations:
                            organization = create_session.query(_Organization).get(organization_id)
                            new_app_user.organizations.append(organization)
                            permissions_manager.assign_user_permission(
                                new_app_user,
                                new_app_user.role,
                                organization.license
                            )

                    # If user has app admin role, assign app admin permission
                    else:
                        permissions_manager.assign_user_permission(new_app_user, new_app_user.role)

                    create_session.add(new_app_user)

                create_session.commit()
                create_session.close()
                return redirect(reverse(next_controller))

        # Get App Users
        session = SessionMaker()
        app_users = session.query(_AppUser).all()

        # Setup portal users select
        all_app_usernames = [u.username for u in app_users]
        all_django_users = User.objects.all()
        portal_users_options = []

        # Options include all users not assigned to the app already
        for django_user in all_django_users:
            if django_user.username not in all_app_usernames:
                portal_users_options.append(
                    (get_display_name_for_django_user(django_user, append_username=True), django_user.username)
                )

        portal_users_options = sorted(portal_users_options, key=lambda u: u[0])

        portal_users_select = SelectInput(
            display_text='Existing User(s)',
            name='portal-users',
            multiple=True,
            initial=selected_portal_users,
            options=portal_users_options,
            error=selected_portal_users_error
        )

        role_select = SelectInput(
            display_text='Role',
            name='assign-role',
            multiple=False,
            initial=selected_role,
            options=role_options,
            error=role_select_error
        )

        organization_select = SelectInput(
            display_text='Organization(s)',
            name='assign-organizations',
            multiple=True,
            initial=selected_organizations,
            options=organization_options,
            error=organization_select_error
        )

        session.close()
        context = {
            'portal_users_select': portal_users_select,
            'role_select': role_select,
            'organization_select': organization_select,
            'next_controller': next_controller,
            'no_organization_roles': no_organization_roles,
            'base_template': self.base_template
        }
        return render(request, 'atcore/app_users/add_existing_user.html', context)
