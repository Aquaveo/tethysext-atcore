"""
********************************************************************************
* Name: resources.py
* Author: msouffront & htran
* Created On: November 20, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import inspect
from django.utils.text import slugify
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import ManageResources, ModifyResource, ResourceDetails, ResourceStatus
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


def urls(url_map_maker, app, persistent_store_name, base_url_path='', base_template='atcore/app_users/base.html',
         custom_controllers=(), custom_models=(), custom_permissions_manager=None, resource_model=Resource):
    """
    Generate UrlMap objects for resources extension. To link to pages provided by the resources extension use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:manage_resources_url %}
        {% url 'my_first_app:edit_resource_url, resource_id=resource.id %}

    Args:
        url_map_maker(UrlMap): UrlMap class bound to app root url.
        app(TethysAppBase): instance of Tethys app class.
        persistent_store_name(str): name of persistent store database setting the controllers should use to create sessions.
        base_url_path(str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        base_template(str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful for customizing styles or overriding navigation of all views.
        custom_controllers(list<TethysController>): Any number of TethysController subclasses to override default controller classes.
        custom_models(list<cls>): custom subclasses of AppUser, Organization, or Resource models.
        custom_permissions_manager(cls): Custom AppPermissionsManager class. Defaults to AppPermissionsManager.
        resource_model(cls): Resource model class. Defaults to Resource.

    Url Map Names:
        app_users_manage_resources
        app_users_new_resource
        app_users_edit_resource <resource_id>
        app_users_resource_details <resource_id>
        app_users_resource_status ?[r=<resource_id>]

    Returns:
        tuple: UrlMap objects for the resources extension.
    """  # noqa: F401, E501
    # Validate kwargs
    if base_url_path:
        if base_url_path.startswith('/'):
            base_url_path = base_url_path[1:]
        if base_url_path.endswith('/'):
            base_url_path = base_url_path[:-1]

    # Default controller classes
    _ManageResources = ManageResources
    _ModifyResource = ModifyResource
    _ResourceDetails = ResourceDetails
    _ResourceStatus = ResourceStatus

    # Default model classes
    _AppUser = AppUser
    _Organization = Organization

    # Default permissions manager
    _PermissionsManager = AppPermissionsManager

    # Handle controller classes
    for custom_controller in custom_controllers:
        if not inspect.isclass(custom_controller) or not issubclass(custom_controller, TethysController):
            raise ValueError('custom_controllers must contain only valid TethysController sub classes.')
        elif issubclass(custom_controller, ManageResources):
            _ManageResources = custom_controller
        elif issubclass(custom_controller, ModifyResource):
            _ModifyResource = custom_controller
        elif issubclass(custom_controller, ResourceDetails):
            _ResourceDetails = custom_controller
        elif issubclass(custom_controller, ResourceStatus):
            _ResourceStatus = custom_controller

    # Handle custom resource model classes
    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, Resource):
            resource_model = custom_model

    # Handle custom permissions manager
    if custom_permissions_manager is not None:
        if inspect.isclass(custom_permissions_manager) and \
           issubclass(custom_permissions_manager, AppPermissionsManager):
            _PermissionsManager = custom_permissions_manager
        else:
            raise ValueError('custom_permissions_manager must be a subclass of AppPermissionsManager.')

    # Url Patterns
    manage_resources_url =              slugify(resource_model.DISPLAY_TYPE_PLURAL.lower())  # noqa: E222
    new_resource_url =                  slugify(resource_model.DISPLAY_TYPE_PLURAL.lower()) + '/new'  # noqa: E222
    edit_resource_url =                 slugify(resource_model.DISPLAY_TYPE_PLURAL.lower()) + '/{resource_id}/edit'  # noqa: E222, E501
    resource_details_url =              slugify(resource_model.DISPLAY_TYPE_PLURAL.lower()) + '/{resource_id}/details'  # noqa: E222, E501
    resource_status_url =               slugify(resource_model.DISPLAY_TYPE_PLURAL.lower()) + '/status'  # noqa: E222

    url_maps = (
        url_map_maker(
            name='app_users_manage_resources',
            url='/'.join([base_url_path, manage_resources_url]) if base_url_path else manage_resources_url,
            controller=_ManageResources.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=resource_model,
                _PermissionsManager=_PermissionsManager,
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
                _Resource=resource_model,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
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
                _Resource=resource_model,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_resource_details',
            url='/'.join([base_url_path, resource_details_url]) if base_url_path else resource_details_url,
            controller=_ResourceDetails.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=resource_model,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        ),
        url_map_maker(
            name='app_users_resource_status',
            url='/'.join([base_url_path, resource_status_url]) if base_url_path else resource_status_url,
            controller=_ResourceStatus.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=resource_model,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template
            )
        )
    )

    return url_maps
