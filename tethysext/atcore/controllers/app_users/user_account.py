"""
********************************************************************************
* Name: user_account
* Author: nswain
* Created On: April 03, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
# Django
from django.shortcuts import render

# Tethys core
from tethys_sdk.base import TethysController
from tethys_sdk.permissions import has_permission
# ATCore
from tethysext.atcore.controllers.app_users.mixins import AppUsersControllerMixin


class UserAccount(TethysController, AppUsersControllerMixin):
    """
    Controller for user_account page.

    GET: Render list of all organizations.
    DELETE: Delete and organization.
    """
    page_title = 'My Account'
    template_name = 'atcore/app_users/user_account.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        """
        Route get requests.
        """
        return self._handle_get(request)

    # @method_decorator(active_user_required) #TODO: Generalize active_user_required
    def _handle_get(self, request, *args, **kwargs):
        """
        Handle get requests.
        """
        _AppUser = self.get_app_user_model()
        _Organization = self.get_organization_model()
        make_session = self.get_sessionmaker()
        session = make_session()

        request_app_user = _AppUser.get_app_user_from_request(request, session)

        if not request_app_user:
            pass

        # Get organizations
        user_organizations = request_app_user.get_organizations(session, request, cascade=False)

        organizations = []
        for user_organization in user_organizations:
            organizations.append({
                'name': user_organization.name,
                'license': _Organization.LICENSES.get_display_name_for(user_organization.license)
            })

        # TODO: Implement with permissions
        permissions_groups = []
        # permissions_groups = get_all_permissions_groups_for_user(django_user, as_display_name=True)

        context = {
            'page_title': self.page_title,
            'username': request_app_user.username,
            'user_role': request_app_user.get_role(display_name=True),
            'user_account_status': 'Active' if request_app_user.is_active else 'Disabled',
            'permissions_groups': permissions_groups,
            'organizations': organizations,
            'show_manage_users_link': has_permission(request, 'view_users'),
            'show_manage_organizations_link': has_permission(request, 'view_organizations')
        }

        session.close()

        return render(request, self.template_name, context)
