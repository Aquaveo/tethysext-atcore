import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import ManageUsers, ModifyUser, AddExistingUser, ManageOrganizations,\
    ManageOrganizationMembers, ModifyOrganization, UserAccount, ManageResources, ModifyResource
from tethysext.atcore.models.app_users import AppUser, Organization, Resource


def urls(url_map_maker, app, persistent_store_name, base_url_path='', base_template='atcore/app_users/base.html',
         custom_controllers=(), custom_models=()):
    """
    Generate UrlMap objects for app_users extension. To link to pages provided by the app_users extension use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:app_users_add_user %}
        {% url 'my_first_app:app_users_edit_user, user_id=user.id %}

    Args:
        url_map_maker(UrlMap): UrlMap class bound to app root url.
        app(TethysAppBase): instance of Tethys app class.
        persistent_store_name(str): name of persistent store database setting the controllers should use to create sessions.
        base_url_path(str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        base_template(str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful to add navigation to ManageUsers, ManageOrganizations, ManageResources, and UserAccount views.
        custom_controllers(list<TethysController>): Any number of TethysController subclasses to override default controller classes.
        custom_models(cls): custom subclasses of AppUser, Organization, or Resource models.

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
        app_users_manage_resources
        app_users_new_resource
        app_users_edit_resource <resource_id>

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
    _ManageResources = ManageResources
    _ModifyResource = ModifyResource

    # Default model classes
    _AppUser = AppUser
    _Organization = Organization
    _Resource = Resource

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
        elif issubclass(custom_controller, ManageResources):
            _ManageResources = custom_controller
        elif issubclass(custom_controller, ModifyResource):
            _ModifyResource = custom_controller

    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, AppUser):
            _AppUser = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Organization):
            _Organization = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Resource):
            _Resource = custom_model
        else:
            raise ValueError('custom_models must contain only subclasses of AppUser, Resources, or Organization.')

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
    manage_resources_url =              _Resource.DISPLAY_TYPE_PLURAL.lower()  # noqa: E222
    new_resource_url =                  _Resource.DISPLAY_TYPE_PLURAL.lower() + '/new'  # noqa: E222
    edit_resource_url =                 _Resource.DISPLAY_TYPE_PLURAL.lower() + '/{resource_id}/edit'  # noqa: E222

    url_maps = (
        url_map_maker(
            name='app_users_manage_users',
            url='/'.join([base_url_path, users_url]) if base_url_path else users_url,
            controller=_ManageUsers.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
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
                _Resource=_Resource
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
                _Resource=_Resource
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
                _Resource=_Resource
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
                _Resource=_Resource,
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
                _Resource=_Resource,
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
                _Resource=_Resource
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
                _Resource=_Resource
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
                _Resource=_Resource
            )
        ),
        url_map_maker(
            name='app_users_manage_resources',
            url='/'.join([base_url_path, manage_resources_url]) if base_url_path else manage_resources_url,
            controller=_ManageResources.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_new_resource',
            url='/'.join([base_url_path, new_resource_url]) if base_url_path else new_resource_url,
            controller=_ModifyResource.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource
            )
        ),
        url_map_maker(
            name='app_users_edit_resource',
            url='/'.join([base_url_path, edit_resource_url]) if base_url_path else edit_resource_url,
            controller=_ModifyResource.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource
            )
        ),
    )

    return url_maps
