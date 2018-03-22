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
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.functional import wraps
from tethys_sdk.permissions import has_permission
from epanet_adapter.project.user_project import Organization, EnterpriseOrganization, UserProject, AppUser
# import tethysapp.epanet.model as app_model
# from tethysapp.epanet.app import UR_ADMIN_DISPLAY, UR_VIEWER_DISPLAY, UR_APP_ADMIN_DISPLAY, STANDARD_VIEWER_ROLE, \
#     STANDARD_ADMIN_ROLE, ADVANCED_VIEWER_ROLE, ADVANCED_ADMIN_ROLE, PROFESSIONAL_VIEWER_ROLE, PROFESSIONAL_ADMIN_ROLE,\
#     ENTERPRISE_ADMIN_ROLE, ENTERPRISE_VIEWER_ROLE, APP_ADMIN_ROLE, PERMISSIONS_GROUP_DISPLAY_NAMES, ADDON_DISPLAY_NAMES, \
#     ADDON_PERMISSIONS_DICT, STAFF_USERNAME
from json import loads


def get_user_enterprise_organizations(session, request_or_user):
    """
    Get the EnterpriseOrganization objects that the given user belongs to.

    Args:
        session: SQLAlchemy session
        request_or_user: Django request object or Django User object

    Returns: List of EnterpriseOrganization objects
    """
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    is_request = False

    if isinstance(request_or_user, HttpRequest):
        is_request = True
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    if user.is_staff or (is_request and has_permission(request_or_user, 'view_all_consultants')):
        return session.query(EnterpriseOrganization).all()

    app_user = session.query(AppUser).filter(AppUser.username == user.username).one_or_none()

    if app_user:
        return session.query(EnterpriseOrganization).filter(EnterpriseOrganization.users.contains(app_user)).all()

    return []


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
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    is_request = False
    return_value = set()
    user_organizations = []

    if isinstance(request_or_user, HttpRequest):
        is_request = True
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    if user.is_staff or (is_request and has_permission(request_or_user, 'view_all_organizations')):
        user_organizations = session.query(Organization).all()

    else:
        app_user = session.query(AppUser).filter(AppUser.username == user.username).one_or_none()

        if app_user:
            user_organizations = app_user.organizations

    organizations = set(user_organizations)

    if cascade:
        for organization in user_organizations:
            if organization.type == app_model.ENTERPRISE_ORG_TYPE:
                organizations.update(organization.clients)

    if as_options:
        for organization in organizations:
            return_value.add((organization.name, str(organization.id)))

        return_value = sorted(return_value, key=lambda c: c[0])
    else:
        return_value = sorted(organizations, key=lambda c: c.name)

    return return_value


def get_display_name_for_django_user(django_user, default_to_username=True, append_username=False):
    """
    Get a nice display name for a django user.
    Args:
        django_user: Django User object.
        default_to_username: Return username if no other names are available if True, otherwise return the empty string.
        append_username: Append the username in parenthesis if True. e.g.: "First Last (username)".

    Returns: In order of priority: "First Last", "First", "Last", "username".

    """
    is_username = False

    if django_user.first_name and django_user.last_name:
        display_name = "{0} {1}".format(django_user.first_name, django_user.last_name)
    elif django_user.first_name:
        display_name = django_user.first_name
    elif django_user.last_name:
        display_name = django_user.last_name
    else:
        is_username = True
        display_name = django_user.username if default_to_username else ""

    if append_username and not is_username:
        display_name += " ({0})".format(django_user.username)
    return display_name


def get_user_projects(session, request):
    """
    Get the projects that the request user is able to assign to clients and consultants.
    Args:
        session: SQLAlchemy session object
        request: Django request object

    Returns:
    """
    projects = set()
    if has_permission(request, 'assign_any_project'):
        projects = session.query(UserProject).all()

    # Other users can only assign projects that belong to his organization or client organizations of his organization
    else:
        app_user = session.query(AppUser).filter(AppUser.username == request.user.username).one_or_none()

        if app_user and app_user.organizations:
            for user_organization in app_user.organizations:
                for project in user_organization.user_projects:
                    projects.add(project)

                if user_organization.type == app_model.ENTERPRISE_ORG_TYPE:
                    for client_organization in user_organization.clients:
                        for client_project in client_organization.user_projects:
                            projects.add(client_project)

    projects = [proj for proj in projects if not proj.is_deleting()]
    projects = sorted(projects, key=lambda p: p.name)

    return projects


def get_assignable_enterprise_organizations(session, request, as_options=False):
    """
    Get enterprise organizations that can be assigned as owner of client organizations.
    Args:
        session: SQLAlchemy session object
        request: Django request object
        as_options: Returns a list of tuple pairs for use as select input options.

    Returns:

    """
    return_value = []

    # Admins (and staff) can assign any consultant to a client
    if request.user.is_staff or has_permission(request, 'assign_any_consultant'):
        consultants = session.query(EnterpriseOrganization).all()
    else:
        consultants = get_user_enterprise_organizations(session, request)

    if as_options:
        for consultant in consultants:
            return_value.append((consultant.name, str(consultant.id)))

        return_value = sorted(return_value, key=lambda c: c[0])
    else:
        return_value = sorted(consultants, key=lambda c: c.name)

    return return_value


def get_assignable_roles(request, as_options=False):
    """
    Get a list of user roles that the request user can assign.
    Args:
        request: Django request object
        as_options: Returns a list of tuple pairs for use as select input options.

    Returns: list of user roles the request user can assign

    """
    roles = []

    if True:
        roles.append(app_model.UR_VIEWER if not as_options else (UR_VIEWER_DISPLAY, app_model.UR_VIEWER))

    if True:
        roles.append(app_model.UR_ADMIN if not as_options else (UR_ADMIN_DISPLAY, app_model.UR_ADMIN))

    if request.user.is_staff or has_permission(request, 'create_app_admin_users'):
        roles.append(app_model.UR_APP_ADMIN if not as_options else (UR_APP_ADMIN_DISPLAY, app_model.UR_APP_ADMIN))

    return roles


def get_role(session, request_or_user, display_name=False):
    """
    Get the most elevated role that has been applied to the given user.

    Args:
        session: SQLAlchemy session object
        request_or_user: Django Request or User object
        display_name: Return display friendly name of role if True.

    Returns: Name of role
    """
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    if isinstance(request_or_user, HttpRequest):
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    app_user = session.query(AppUser).filter(AppUser.username == user.username).one_or_none()

    if app_user.role == app_model.UR_APP_ADMIN:
        return app_model.UR_APP_ADMIN if not display_name else UR_APP_ADMIN_DISPLAY

    if app_user.role == app_model.UR_ADMIN:
        return app_model.UR_ADMIN if not display_name else UR_ADMIN_DISPLAY

    if app_user.role == app_model.UR_VIEWER:
        return app_model.UR_VIEWER if not display_name else UR_VIEWER_DISPLAY

    return ""


def add_permissions_group(user, permissions_group_name):
    """
    Add the user to the role/group with the given name.
    Args:
        user: Django User object
        permissions_group_name: Name of group to add
    """
    from django.contrib.auth.models import Group
    group = Group.objects.get(name=permissions_group_name)
    group.user_set.add(user)


def remove_permissions_group(user, permissions_group_name):
    """
    Remove the user from the role/group with the given name.
    Args:
        user: Django User object
        permissions_group_name: Name of group to remove
    """
    from django.contrib.auth.models import Group
    group = Group.objects.get(name=permissions_group_name)
    group.user_set.remove(user)


def remove_all_epanet_permissions_groups(user):
    """
    Remove the user from all epanet roles/groups.
    Args:
        user:  Django User object
    """
    from django.contrib.auth.models import Group
    groups = Group.objects.filter(name__icontains='epanet:')
    for group in groups:
        group.user_set.remove(user)


def get_all_permissions_groups_for_user(user, as_display_name=False):
    """

    Args:
        user: Django User object.
        as_display_name: Returns display names instead of programmatic name if True.

    Returns: Returns a list of all epanet permissions group objects for this user.
    """
    if user.is_staff:
        from django.contrib.auth.models import Group
        user_groups = Group.objects.filter(name__icontains='epanet:').values_list('name', flat=True).order_by('-name')
    else:
        user_groups = user.groups.filter(name__icontains='epanet:').values_list('name', flat=True).order_by('-name')

    groups = []

    for user_group in user_groups:
        groups.append(PERMISSIONS_GROUP_DISPLAY_NAMES[user_group] if as_display_name else user_group)

    return groups


def get_user_peers(session, request, include_self=False, cascade=False):
    """
    Get AppUsers belong to organizations to which the request user belongs.
    Args:
        session: SQLAlchemy session object.
        request: Django request object.
        cascade: Get users of client organizations if True.

    Returns: A list of AppUser objects.
    """
    if request.user.is_staff or has_permission(request, 'assign_any_user'):
        return session.query(AppUser).all()

    manageable_users = set()
    organizations = get_user_organizations(session, request, cascade=cascade)

    for organization in organizations:
        for user in organization.users:
            # Don't add self to manage users
            if user.username != request.user.username:
                manageable_users.add(user)
            elif include_self:
                manageable_users.add(user)
    return manageable_users


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
    # Staff can always do this
    if request.user.is_staff:
        return True

    # First check permissions
    if not has_permission(request, 'modify_organizations'):
        return False

    # Then check to see whether there is "room"
    enterprise_orgs = get_user_enterprise_organizations(session, request)
    num_maxed_out_orgs = 0

    for enterprise_org in enterprise_orgs:
        max_clients = enterprise_org.get_max_clients_at_level(level)

        # Check for unlimited max clients
        if max_clients == app_model.UNLIMITED_MAX_CLIENTS:
            return True

        if max_clients == 0:
            num_maxed_out_orgs += 1
            continue

        clients = enterprise_org.clients
        for client in clients:
            num_clients = 0
            if client.type == app_model.CLIENT_ORG_TYPE and client.access_level == level:
                num_clients += 1
                if num_clients >= max_clients:
                    num_maxed_out_orgs += 1
                    continue

    if num_maxed_out_orgs >= len(enterprise_orgs):
        return False

    return True


def get_owner_options_and_mapping(session, request, license_options):
    license_to_owner_options_mapping = {}
    owner_options = set()
    enterprise_orgs = get_assignable_enterprise_organizations(session, request)
    can_assign_to_all_orgs = request.user.is_staff or has_permission(request, 'assign_any_consultant')

    for license_option in license_options:
        LICENSE = license_option[1]
        license_to_owner_options_mapping[LICENSE] = []
        for enterprise_org in enterprise_orgs:
            # Staff can assign to any owner
            if request.user.is_staff:
                owner_options.add((enterprise_org.name, str(enterprise_org.id)))
                license_to_owner_options_mapping[LICENSE].append(str(enterprise_org.id))
                continue

            # Check for unlimited max clients
            if enterprise_org.get_max_clients_at_level(LICENSE) == app_model.UNLIMITED_MAX_CLIENTS or \
                    can_assign_to_all_orgs:
                owner_options.add((enterprise_org.name, str(enterprise_org.id)))
                license_to_owner_options_mapping[LICENSE].append(str(enterprise_org.id))
                continue

            clients = enterprise_org.clients
            num_licensed = 0
            for client in clients:
                if client.type == app_model.CLIENT_ORG_TYPE and client.access_level == LICENSE:
                    num_licensed += 1
            if num_licensed <= enterprise_org.get_max_clients_at_level(LICENSE) or can_assign_to_all_orgs:
                owner_options.add((enterprise_org.name, str(enterprise_org.id)))
                license_to_owner_options_mapping[LICENSE].append(str(enterprise_org.id))

    return list(owner_options), license_to_owner_options_mapping


def assign_user_permission(request_or_user, user_role, license=None, addons=None):
    """
    Add permissions based on combo of user_role and level
    Args:
        request_or_user: Django Request or User object.
        user_role: Role of user (Admin, Viewer, or App Admin).
        license: License or access level of permission (Standard, Professional, Enterprise).
    """
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    if isinstance(request_or_user, HttpRequest):
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    # Handle all permutations
    if user_role == app_model.UR_VIEWER:
        if license == app_model.ACCESS_STANDARD:
            add_permissions_group(user, STANDARD_VIEWER_ROLE)
        elif license == app_model.ACCESS_ADVANCED:
            add_permissions_group(user, ADVANCED_VIEWER_ROLE)
        elif license == app_model.ACCESS_PROFESSIONAL:
            add_permissions_group(user, PROFESSIONAL_VIEWER_ROLE)
        elif license == app_model.ACCESS_ENTERPRISE:
            add_permissions_group(user, ENTERPRISE_VIEWER_ROLE)

    elif user_role == app_model.UR_ADMIN:
        if license == app_model.ACCESS_STANDARD:
            add_permissions_group(user, STANDARD_ADMIN_ROLE)
        elif license == app_model.ACCESS_ADVANCED:
            add_permissions_group(user, ADVANCED_ADMIN_ROLE)
        elif license == app_model.ACCESS_PROFESSIONAL:
            add_permissions_group(user, PROFESSIONAL_ADMIN_ROLE)
        elif license == app_model.ACCESS_ENTERPRISE:
            add_permissions_group(user, ENTERPRISE_ADMIN_ROLE)

    elif user_role == app_model.UR_APP_ADMIN:
        add_permissions_group(user, APP_ADMIN_ROLE)

    if addons:
        update_addon_permissions_for_user(user, user_role, addons)

    user.save()


def remove_user_permission(request_or_user, user_role, license=None):
    """
    Remove permissions based on combo of user_role and level
    Args:
        request_or_user: Django Request or User object.
        user_role: Role of user (Admin, Viewer, or App Admin).
        license: License or access level of permission (Standard, Professional, Enterprise).
    """
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    if isinstance(request_or_user, HttpRequest):
        user = request_or_user.user
    elif isinstance(request_or_user, User):
        user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    # Handle all permutations
    if user_role == app_model.UR_VIEWER:
        if license == app_model.ACCESS_STANDARD:
            remove_permissions_group(user, STANDARD_VIEWER_ROLE)
        elif license == app_model.ACCESS_PROFESSIONAL:
            remove_permissions_group(user, PROFESSIONAL_VIEWER_ROLE)
        elif license == app_model.ACCESS_ENTERPRISE:
            remove_permissions_group(user, ENTERPRISE_VIEWER_ROLE)

    elif user_role == app_model.UR_ADMIN:
        if license == app_model.ACCESS_STANDARD:
            remove_permissions_group(user, STANDARD_ADMIN_ROLE)
        elif license == app_model.ACCESS_PROFESSIONAL:
            remove_permissions_group(user, PROFESSIONAL_ADMIN_ROLE)
        elif license == app_model.ACCESS_ENTERPRISE:
            remove_permissions_group(user, ENTERPRISE_ADMIN_ROLE)

    elif user_role == app_model.UR_APP_ADMIN:
        remove_permissions_group(user, APP_ADMIN_ROLE)

    user.save()


def update_user_permissions(session, request_or_user):
    """
    Update permissions for user. Permissions are a combination of the user's role (Admin, Viewer, or App Admin), and
    the license of the organizations the user belongs to (Standard, Professional, Enterprise).
    Args:
        session: SQLAlchemy session object.
        request_or_user: Django Request or User object.
    """
    from django.contrib.auth.models import User
    from django.http.request import HttpRequest

    if isinstance(request_or_user, HttpRequest):
        django_user = request_or_user.user
    elif isinstance(request_or_user, User):
        django_user = request_or_user
    else:
        raise TypeError('request_or_user must be a Django request or User instance.')

    app_user = session.query(AppUser).filter(AppUser.username == django_user.username).one_or_none()

    # Could be a developer/staff user that isn't registered with app
    if not app_user:
        # Do nothing for developer/staff users.
        return

    # Clear all epanet permissions
    remove_all_epanet_permissions_groups(django_user)

    # Get user role
    user_role = app_user.role

    # App admins shouldn't belong to any organizations (i.e.: have license restrictions)
    if user_role == app_model.UR_APP_ADMIN:
        # Clear organizations
        app_user.organizations = []

        # Assign permissions
        assign_user_permission(django_user, user_role)

    # Other user roles belong to organizations, which impose license restrictions
    # Assign permissions according to organization membership
    for organization in app_user.organizations:
        assign_user_permission(django_user, user_role, organization.access_level, organization.addons)

    session.commit()
    django_user.save()


def update_addon_permissions_for_user(user_obj, user_role, addons):
    from django.contrib.auth.models import User

    user = user_obj if isinstance(user_obj, User) else User.objects.get(username=user_obj.username)
    addons_dict = loads(addons) if not isinstance(addons, dict) else addons

    for addon_id in addons_dict:
        for perm in ADDON_PERMISSIONS_DICT[addon_id][user_role]:
            if user_role == app_model.UR_APP_ADMIN or addons_dict[addon_id]['enabled']:
                add_permissions_group(user, perm)
            else:
                remove_permissions_group(user, perm)


def update_addon_permissions_for_organization(session, organization, addons_dict):
    org_users = session.query(AppUser).filter(AppUser.organizations.contains(organization))

    for org_user in org_users:
        user_role = org_user.role.lower()
        update_addon_permissions_for_user(org_user, user_role, addons_dict)


def get_default_addons_dict():
    addons_dict = {}
    for name in ADDON_DISPLAY_NAMES:
        addons_dict[name] = {
            'title': ADDON_DISPLAY_NAMES[name],
            'enabled': False
        }

    return addons_dict


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
    for app_user in organization.users:
        django_user = app_user.get_django_user()
        if django_user is None:
            continue
        is_active = False
        for org in get_user_organizations(session, django_user):
            if org.active:
                is_active = True
                break
        app_user.is_active = is_active
        session.commit()


def get_app_user_from_request(request, session=None):
    from tethysapp.epanet.model import SessionMaker, AppUser
    close_session = session is None

    if not session:
        session = SessionMaker()

    if request.user.is_staff:
        username = STAFF_USERNAME
    else:
        username = request.user.username

    app_user = session.query(AppUser).filter(AppUser.username == username).one_or_none()

    if close_session:
        session.close()

    return app_user
