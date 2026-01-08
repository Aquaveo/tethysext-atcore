"""
********************************************************************************
* Name: resources.py
* Author: msouffront & htran
* Created On: November 20, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""

import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import (
    ManageResources,
    ModifyResource,
    ResourceDetails,
    ResourceStatus,
)
from tethysext.atcore.models.app_users import AppUser, Organization, Resource
from tethysext.atcore.services.app_users.permissions_manager import (
    AppPermissionsManager,
)
from tethysext.atcore.utilities import update_urlmap_index


def urls(
    url_map_maker,
    app,
    persistent_store_name,
    base_url_path="",
    base_template="atcore/app_users/base.html",
    custom_controllers=(),
    custom_models=(),
    custom_permissions_manager=None,
    resource_model=Resource,
):
    """
    Generate UrlMap objects for Resource Views. To link to pages provided by the Resource Views use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:manage_resources_url %}
        {% url 'my_first_app:edit_resource_url, resource_id=resource.id %}

    Args:
        url_map_maker (UrlMap): UrlMap class bound to app root url.
        app (TethysAppBase): instance of Tethys app class.
        persistent_store_name (str): name of persistent store database setting the controllers should use to create sessions.
        base_url_path (str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        base_template (str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful for customizing styles or overriding navigation of all views.
        custom_controllers (list<TethysController>): Any number of TethysController subclasses to override default controller classes.
        custom_models (list<cls>): custom subclasses of AppUser or Organization models.
        custom_permissions_manager (cls): Custom AppPermissionsManager class. Defaults to AppPermissionsManager.
        resource_model (Resource): Resource model class. Defaults to Resource.

    Url Map Names:
        <resource_slug>_manage_resources
        <resource_slug>_new_resource
        <resource_slug>_edit_resource <resource_id>
        <resource_slug>_resource_details <resource_id>
        <resource_slug>_resource_status <resource_id>
        <resource_slug>_resource_status_list

    Returns:
        tuple: UrlMap objects for the Resource Views.
    """  # noqa: F401, E501
    # Validate kwargs
    if base_url_path:
        if base_url_path.startswith("/"):
            base_url_path = base_url_path[1:]
        if base_url_path.endswith("/"):
            base_url_path = base_url_path[:-1]

    # Default controller classes
    _ManageResources = ManageResources
    _ModifyResource = ModifyResource
    _ResourceDetails = ResourceDetails
    _ResourceStatus = ResourceStatus

    # Default model classes
    _AppUser = AppUser
    _Organization = Organization
    _Resource = Resource

    # Default permissions manager
    _PermissionsManager = AppPermissionsManager

    # Handle controller classes
    for custom_controller in custom_controllers:
        if not inspect.isclass(custom_controller) or not issubclass(
            custom_controller, TethysController
        ):
            raise ValueError(
                "custom_controllers must contain only valid TethysController sub classes."
            )
        elif issubclass(custom_controller, ManageResources):
            _ManageResources = custom_controller
        elif issubclass(custom_controller, ModifyResource):
            _ModifyResource = custom_controller
        elif issubclass(custom_controller, ResourceDetails):
            _ResourceDetails = custom_controller
        elif issubclass(custom_controller, ResourceStatus):
            _ResourceStatus = custom_controller

    # Handle custom model classes
    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, AppUser):
            _AppUser = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Organization):
            _Organization = custom_model
        else:
            raise ValueError(
                "custom_models must contain only subclasses of AppUser or Organization."
            )

    # Handle resource model
    if inspect.isclass(resource_model) and issubclass(resource_model, Resource):
        _Resource = resource_model
    else:
        raise ValueError("resource_model must be a subclass of Resource.")

    # Handle custom permissions manager
    if custom_permissions_manager is not None:
        if inspect.isclass(custom_permissions_manager) and issubclass(
            custom_permissions_manager, AppPermissionsManager
        ):
            _PermissionsManager = custom_permissions_manager
        else:
            raise ValueError(
                "custom_permissions_manager must be a subclass of AppPermissionsManager."
            )

    # Url Patterns
    manage_resources_url = resource_model.SLUG.replace("_", "-")
    new_resource_url = manage_resources_url + "/new"
    edit_resource_url = manage_resources_url + "/{resource_id}/edit"
    resource_details_url = manage_resources_url + "/{resource_id}/details"
    resource_status_list_url = manage_resources_url + "/status"
    resource_status_url = manage_resources_url + "/{resource_id}/status" 

    url_maps = (
        url_map_maker(
            name=f"{resource_model.SLUG}_manage_resources",
            url=(
                "/".join([base_url_path, manage_resources_url])
                if base_url_path
                else manage_resources_url
            ),
            controller=_ManageResources.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
        url_map_maker(
            name=f"{resource_model.SLUG}_new_resource",
            url=(
                "/".join([base_url_path, new_resource_url])
                if base_url_path
                else new_resource_url
            ),
            controller=_ModifyResource.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
        url_map_maker(
            name=f"{resource_model.SLUG}_edit_resource",
            url=(
                "/".join([base_url_path, edit_resource_url])
                if base_url_path
                else edit_resource_url
            ),
            controller=_ModifyResource.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
        url_map_maker(
            name=f"{resource_model.SLUG}_resource_details",
            url=(
                "/".join([base_url_path, resource_details_url])
                if base_url_path
                else resource_details_url
            ),
            controller=_ResourceDetails.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
        url_map_maker(
            name=f"{resource_model.SLUG}_resource_status",
            url=(
                "/".join([base_url_path, resource_status_url])
                if base_url_path
                else resource_status_url
            ),
            controller=_ResourceStatus.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
        url_map_maker(
            name=f"{resource_model.SLUG}_resource_status_list",
            url=(
                "/".join([base_url_path, resource_status_list_url])
                if base_url_path
                else resource_status_list_url
            ),
            controller=_ResourceStatus.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _AppUser=_AppUser,
                _Organization=_Organization,
                _Resource=_Resource,
                _PermissionsManager=_PermissionsManager,
                base_template=base_template,
            ),
        ),
    )

    url_maps = update_urlmap_index(url_maps, app)

    return url_maps
