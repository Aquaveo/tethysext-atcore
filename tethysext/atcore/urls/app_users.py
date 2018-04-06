import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import ManageUsers, ModifyUser, AddExistingUser, ManageOrganizations,\
    ManageOrganizationMembers, ModifyOrganization, UserAccount
from tethysext.atcore.models.app_users import AppUser, Organization, Resource


def urls(url_map_maker, base_url_path='', base_template='atcore/app_users/base.html', app=None,
         persistent_store_name=None, custom_controllers=(), custom_models=()):
    """
    Generate UrlMap objects for app_users extension. To link to pages provided by the app_users extension use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:app_users_add_user %}
        {% url 'my_first_app:app_users_edit_user, user_id=user.id %}

    Args:
        url_map_maker(UrlMap): UrlMap class bound to app root url.
        base_url_path(str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        base_template(str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful to add navigation to ManageUsers, ManageOrganizations, ManageResources, and UserAccount views.
        app(TethysAppBase): instance of Tethys app class.
        persistent_store_name(str): name of persistent store database setting the controllers should use to create sessions.
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

    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, AppUser):
            _AppUser = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Organization):
            _Organization = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Resource):
            _Resource = custom_model
        else:
            raise ValueError('custom_models must contain only subclasses of AppUser, Resources, or Organization.')

    url_maps = (
        url_map_maker(
            name='app_users_manage_users',
            url='/'.join([base_url_path, 'users']) if base_url_path else 'users',
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
            url='/'.join([base_url_path, 'users/new']) if base_url_path else 'users/new',
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
            url='/'.join([base_url_path, 'users/{user_id}/edit']) if base_url_path else 'users/{user_id}/edit',
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
            url='/'.join([base_url_path, 'users/add-existing']) if base_url_path else 'users/add-existing',
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
            url='/'.join([base_url_path, 'users/me']) if base_url_path else 'users/me',
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
            url='/'.join([base_url_path, 'organizations']) if base_url_path else 'organizations',
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
            url='/'.join([base_url_path, 'organizations/{organization_id}/members']) if base_url_path else 'organizations/{organization_id}/members',  # noqa: E501
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
            url='/'.join([base_url_path, 'organizations/new']) if base_url_path else 'organizations/new',
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
            url='/'.join([base_url_path, 'organizations/{organization_id}/edit']) if base_url_path else 'organizations/{organization_id}/edit',  # noqa: E501
            controller=_ModifyOrganization.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource
            )
        )
    )

    return url_maps
