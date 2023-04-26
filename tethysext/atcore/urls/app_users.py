"""
********************************************************************************
* Name: app_users.py
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import ManageUsers, ModifyUser, AddExistingUser, ManageOrganizations,\
    ManageOrganizationMembers, ModifyOrganization, UserAccount
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.urls import resources


def urls(url_map_maker, app, persistent_store_name, base_url_path='', base_template='atcore/app_users/base.html',
         custom_controllers=(), custom_models=(), custom_resources=(), custom_permissions_manager=None):
    """
    Generate UrlMap objects for app_users extension. To link to pages provided by the app_users extension use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:app_users_add_user %}
        {% url 'my_first_app:app_users_edit_user, user_id=user.id %}

    Args:
        url_map_maker (UrlMap): UrlMap class bound to app root url.
        app (TethysAppBase): instance of Tethys app class.
        persistent_store_name (str): name of persistent store database setting the controllers should use to create sessions.
        base_url_path (str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        base_template (str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful for customizing styles or overriding navigation of all views.
        custom_controllers (list<TethysController>): Any number of TethysController subclasses to override default controller classes.
        custom_models (list<cls>): custom subclasses of AppUser or Organization models.
        custom_resources (list<Resource>): custom subclasses of Resource models.
        custom_permissions_manager (cls): Custom AppPermissionsManager class. Defaults to AppPermissionsManager.

    Url Map Names:
        app_users_manage_users
        app_users_add_user
        app_users_edit_user <user_id>
        app_users_add_existing_user
        app_users_user_account
        app_users_manage_organizations
        app_users_manage_organization_members <organization_id>
        app_users_new_organization
        app_users_edit_organization <organization_id>
        
    Url Map Names for each Resource given:
        <resource_slug>_manage_resources
        <resource_slug>_new_resource
        <resource_slug>_edit_resource <resource_id>
        <resource_slug>_resource_details <resource_id>
        <resource_slug>_resource_status ?[r=<resource_id>]

    Returns:
        tuple: UrlMap objects for the app_users extension.
    """  # noqa: F401, E501
    # Validate kwargs
    if base_url_path:
        if base_url_path.startswith('/'):
            base_url_path = base_url_path[1:]
        if base_url_path.endswith('/'):
            base_url_path = base_url_path[:-1]

    # Default controller classes
    _ManageUsers = ManageUsers
    _ModifyUser = ModifyUser
    _AddExistingUser = AddExistingUser
    _ManageOrganizations = ManageOrganizations
    _ManageOrganizationMembers = ManageOrganizationMembers
    _ModifyOrganization = ModifyOrganization
    _UserAccount = UserAccount

    # Default model classes
    _AppUser = AppUser
    _Organization = Organization
    _Resources = [Resource]

    # Default permissions manager
    _PermissionsManager = AppPermissionsManager

    # Handle controller classes
    for custom_controller in custom_controllers:
        if not inspect.isclass(custom_controller) or not issubclass(custom_controller, TethysController):
            raise ValueError('custom_controllers must contain only valid TethysController sub classes.')
        elif issubclass(custom_controller, ManageUsers):
            _ManageUsers = custom_controller
        elif issubclass(custom_controller, ModifyUser):
            _ModifyUser = custom_controller
        elif issubclass(custom_controller, AddExistingUser):
            _AddExistingUser = custom_controller
        elif issubclass(custom_controller, ManageOrganizations):
            _ManageOrganizations = custom_controller
        elif issubclass(custom_controller, ManageOrganizationMembers):
            _ManageOrganizationMembers = custom_controller
        elif issubclass(custom_controller, ModifyOrganization):
            _ModifyOrganization = custom_controller
        elif issubclass(custom_controller, UserAccount):
            _UserAccount = custom_controller

    # Handle custom model classes
    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, AppUser):
            _AppUser = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Organization):
            _Organization = custom_model
        else:
            raise ValueError('custom_models must contain only subclasses of AppUser or Organization.')

    # Handle custom resource classes
    for custom_resource in custom_resources:
        if inspect.isclass(custom_resource) and issubclass(custom_resource, Resource):
            _Resources.append(custom_resource)
        else:
            raise ValueError('custom_resources must contain only subclasses of Resource.')

    # Remove default Resource class
    if len(_Resources) > 1:
        _Resources.pop(0)

    # Handle custom permissions manager
    if custom_permissions_manager is not None:
        if inspect.isclass(custom_permissions_manager) and \
           issubclass(custom_permissions_manager, AppPermissionsManager):
            _PermissionsManager = custom_permissions_manager
        else:
            raise ValueError('custom_permissions_manager must be a subclass of AppPermissionsManager.')

    # Url Patterns
    users_url =                         'users'  # noqa: E222
    new_user_url =                      'users/new'  # noqa: E222
    add_existing_user_url =             'users/add-existing'  # noqa: E222
    edit_user_url =                     'users/{user_id}/edit'  # noqa: E222
    user_account_url =                  'users/me'  # noqa: E222
    organizations_url =                 'organizations'  # noqa: E222
    new_organization_url =              'organizations/new'  # noqa: E222
    edit_organization_url =             'organizations/{organization_id}/edit'  # noqa: E222
    manage_organization_members_url =   'organizations/{organization_id}/members'  # noqa: E222

    url_maps = [
        url_map_maker(
            name='app_users_manage_users',
            url='/'.join([base_url_path, users_url]) if base_url_path else users_url,
            controller=_ManageUsers.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_add_user',
            url='/'.join([base_url_path, new_user_url]) if base_url_path else new_user_url,
            controller=_ModifyUser.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_edit_user',
            url='/'.join([base_url_path, edit_user_url]) if base_url_path else edit_user_url,
            controller=_ModifyUser.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_add_existing_user',
            url='/'.join([base_url_path, add_existing_user_url]) if base_url_path else add_existing_user_url,
            controller=_AddExistingUser.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_user_account',
            url='/'.join([base_url_path, user_account_url]) if base_url_path else user_account_url,
            controller=_UserAccount.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_manage_organizations',
            url='/'.join([base_url_path, organizations_url]) if base_url_path else organizations_url,
            controller=_ManageOrganizations.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resources=_Resources,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_manage_organization_members',
            url='/'.join([base_url_path, manage_organization_members_url]) if base_url_path else manage_organization_members_url,  # noqa: E501
            controller=_ManageOrganizationMembers.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_new_organization',
            url='/'.join([base_url_path, new_organization_url]) if base_url_path else new_organization_url,
            controller=_ModifyOrganization.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resources=_Resources,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_edit_organization',
            url='/'.join([base_url_path, edit_organization_url]) if base_url_path else edit_organization_url,
            controller=_ModifyOrganization.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resources=_Resources,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        )
    ]

    for _Resource in _Resources:
        resources_urls = resources.urls(
            url_map_maker=url_map_maker,
            app=app,
            persistent_store_name=persistent_store_name,
            base_url_path=base_url_path,
            base_template=base_template,
            custom_controllers=custom_controllers,
            custom_models=custom_models,
            custom_permissions_manager=custom_permissions_manager,
            resource_model=_Resource
        )

        url_maps.extend(resources_urls)

    return url_maps
