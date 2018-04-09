# flake8:noqa
"""
********************************************************************************
* Name: user_group_helpers.py
* Author: nswain
* Created On: July 26, 2016
* Copyright: (c) Aquaveo 2016
* License:
********************************************************************************
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import wraps


# from epanet_adapter.project.user_project import Organization, EnterpriseOrganization, UserProject, AppUser
# import tethysapp.epanet.model as app_model
# from tethysapp.epanet.app import UR_ADMIN_DISPLAY, UR_VIEWER_DISPLAY, UR_APP_ADMIN_DISPLAY, STANDARD_VIEWER_ROLE, \
#     STANDARD_ADMIN_ROLE, ADVANCED_VIEWER_ROLE, ADVANCED_ADMIN_ROLE, PROFESSIONAL_VIEWER_ROLE, PROFESSIONAL_ADMIN_ROLE,\
#     ENTERPRISE_ADMIN_ROLE, ENTERPRISE_VIEWER_ROLE, APP_ADMIN_ROLE, PERMISSIONS_GROUP_DISPLAY_NAMES, ADDON_DISPLAY_NAMES, \
#     ADDON_PERMISSIONS_DICT, STAFF_USERNAME


def get_user_organizations(session, request_or_user, as_options=False, cascade=False):
    """
    Get the Organizations to which the given user belongs.
    Args:
        session: SQLAlchemy session object.
        request_or_user: Django Request or User object
        as_options: Return and select option pairs if True.
        cascade: Return client organizations if True.

    Returns:

    """
    # TODO: Replace instances with app_user.get_organizations()


def get_user_projects(session, request):
    """
    Get the projects that the request user is able to assign to clients and consultants.
    Args:
        session: SQLAlchemy session object
        request: Django request object

    Returns:
    """
    # TODO: Replace instances with app_user.get_resources()


def get_assignable_roles(request, as_options=False):
    """
    Get a list of user roles that the request user can assign.
    Args:
        request: Django request object
        as_options: Returns a list of tuple pairs for use as select input options.

    Returns: list of user roles the request user can assign

    """
    # TODO: Replace instances with app_user.get_assignable_roles()
    # roles = []
    #
    # if True:
    #     roles.append(app_model.UR_VIEWER if not as_options else (UR_VIEWER_DISPLAY, app_model.UR_VIEWER))
    #
    # if True:
    #     roles.append(app_model.UR_ADMIN if not as_options else (UR_ADMIN_DISPLAY, app_model.UR_ADMIN))
    #
    # if request.user.is_staff or has_permission(request, 'create_app_admin_users'):
    #     roles.append(app_model.UR_APP_ADMIN if not as_options else (UR_APP_ADMIN_DISPLAY, app_model.UR_APP_ADMIN))
    #
    # return roles


def get_role(session, request_or_user, display_name=False):
    """
    Get the most elevated role that has been applied to the given user.

    Args:
        session: SQLAlchemy session object
        request_or_user: Django Request or User object
        display_name: Return display friendly name of role if True.

    Returns: Name of role
    """
    # TODO: Replaces instances with app_user.get_role


def add_permissions_group(user, permissions_group_name):
    """
    Add the user to the role/group with the given name.
    Args:
        user: Django User object
        permissions_group_name: Name of group to add
    """
    # TODO: Replace instances with app_permissions_manager.add_permissions_group()


def remove_permissions_group(user, permissions_group_name):
    """
    Remove the user from the role/group with the given name.
    Args:
        user: Django User object
        permissions_group_name: Name of group to remove
    """
    # TODO: Replace instances with app_permissions_manager.remove_permissions_group()


def remove_all_epanet_permissions_groups(user):
    """
    Remove the user from all epanet roles/groups.
    Args:
        user:  Django User object
    """
    # TODO: Replace instances with app_permissions_manager.remove_all_permissions_groups()


def get_all_permissions_groups_for_user(user, as_display_name=False):
    """

    Args:
        user: Django User object.
        as_display_name: Returns display names instead of programmatic name if True.

    Returns: Returns a list of all epanet permissions group objects for this user.
    """
    # TODO: Replace instances with app_permissions_manager.get_all_permissions_groups_for()


def get_user_peers(session, request, include_self=False, cascade=False):
    """
    Get AppUsers belong to organizations to which the request user belongs.
    Args:
        session: SQLAlchemy session object.
        request: Django request object.
        cascade: Get users of client organizations if True.

    Returns: A list of AppUser objects.
    """
    # TODO: Replace instances with app_user.get_peers()


def is_app_user(session, request):
    """
    Returns true if the request user is also an AppUser.
    Args:
        session: SQLAlchemy session object.
        request: Django request object.

    Returns: True if the request user is an AppUser, otherwise False.
    """
    # Staff members always allowed to access
    if request.user.is_staff:
        return True

    # Get AppUser
    app_user = session.query(AppUser).filter(AppUser.username == request.user.username).one_or_none()
    if app_user is not None:
        return True
    return False


def cleanup_and_redirect(session, request):
    """
    Cleanup the session and generate the redirect to the apps page with warning message.
    Args:
        session: SQLAlchemy session object.
        request: Django request object.

    Returns: Django redirect object.
    """
    messages.warning(request, "We're sorry, but you are not allowed access to the CityWater app.")
    session.close()
    return redirect(reverse('app_library'))


def can_create_client_organizations_at_level(session, request, level):
    """
    Determine whether the user is able to create standard organizations.
    Args:
        session: SQLAlchemy session object.
        request: Django request object.

    Returns: True when the user is able to create standard organizations.
    """
    # TODO: refactor to Licenses.get_assign_permission_for() methodology. See: ModifyOrganization controller for example.


def get_owner_options_and_mapping(session, request, license_options):
    # TODO: refactored to app_users.get_organizations(consultants=True) and ModifyOrganization.get_get_license_to_consultant_map
    pass


def assign_user_permission(request_or_user, user_role, license=None, addons=None):
    """
    Add permissions based on combo of user_role and level
    Args:
        request_or_user: Django Request or User object.
        user_role: Role of user (Admin, Viewer, or App Admin).
        license: License or access level of permission (Standard, Professional, Enterprise).
    """
    # TODO: Replace instances with app_permissions_manager.assign_user_permission()


def remove_user_permission(request_or_user, user_role, license=None):
    """
    Remove permissions based on combo of user_role and level
    Args:
        request_or_user: Django Request or User object.
        user_role: Role of user (Admin, Viewer, or App Admin).
        license: License or access level of permission (Standard, Professional, Enterprise).
    """
    # TODO: Replace instances with app_permissions_manager.remove_user_permission()


def update_user_permissions(session, request_or_user):
    """
    Update permissions for user. Permissions are a combination of the user's role (Admin, Viewer, or App Admin), and
    the license of the organizations the user belongs to (Standard, Professional, Enterprise).
    Args:
        session: SQLAlchemy session object.
        request_or_user: Django Request or User object.
    """
    # TODO: Replace instances with app_user.update_permissions()


def active_user_required(*args, **kwargs):
    def decorator(controller_func):
        @login_required()
        def _wrapped_controller(request, *args, **kwargs):
            if not request.user.is_staff:
                from tethysapp.epanet.model import SessionMaker, AppUser
                session = SessionMaker()
                app_user = session.query(AppUser).filter(AppUser.username == request.user.username).one_or_none()
                session.close()
                if app_user is None:
                    messages.warning(request, "We're sorry, but you are not allowed access to the CityWater app.")
                    return redirect(reverse('app_library'))
                else:
                    if app_user.is_active is False:
                        messages.warning(request, "We're sorry, but your CityWater account has been disabled. "
                                                  "Please contact your organization's CityWater admin for further "
                                                  "questions and assistance.")
                        return redirect(reverse('app_library'))
            return controller_func(request, *args, **kwargs)
        return wraps(controller_func)(_wrapped_controller)
    return decorator


def modify_account_status_of_unique_users_of_organization(session, organization):
    # TODO: replace instances with organization.update_member_activity
    pass


def get_app_user_from_request(request, session=None):
    """
    """
    # TODO: replace instances with AppUser.get_app_user_from_request
