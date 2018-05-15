import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.services.spatial_reference import SpatialReferenceService
from tethysext.atcore.controllers.rest.spatial_reference import QuerySpatialReference


def urls(url_map_maker, app, persistent_store_name, base_url_path='', custom_controllers=(), custom_services=()):
    """
    Generate UrlMap objects for spatial_reference_select gizmo.

    ::

        {% url 'my_first_app:app_users_add_user %}
        {% url 'my_first_app:app_users_edit_user, user_id=user.id %}

    Args:
        url_map_maker(UrlMap): UrlMap class bound to app root url.
        app(TethysAppBase): instance of Tethys app class.
        persistent_store_name(str): name of persistent store database setting the controllers should use to create sessions.
        base_template(str): relative path to base template (e.g.: 'my_first_app/base.html'). Useful to add navigation to ManageUsers, ManageOrganizations, ManageResources, and UserAccount views.
        custom_controllers(list<TethysController>): Any number of TethysController subclasses to override default controller classes.
        custom_services(cls): custom subclasses of SpatialRefereceService service.

    Url Map Names:
        atcore_query_spatial_reference

    Returns:
        tuple: UrlMap objects for the spatial reference gizmo.
    """  # noqa: F401, E501

    # Default controller classes
    _QuerySpatialReference = QuerySpatialReference

    # Default model classes
    _SpatialReferenceService = SpatialReferenceService

    # Handle controller classes
    for custom_controller in custom_controllers:
        if not inspect.isclass(custom_controller) or not issubclass(custom_controller, TethysController):
            raise ValueError('custom_controllers must contain only valid TethysController sub classes.')
        elif issubclass(custom_controller, QuerySpatialReference):
            _QuerySpatialReference = custom_controller

    for custom_service in custom_services:
        if inspect.isclass(custom_service) and issubclass(custom_service, SpatialReferenceService):
            _SpatialReferenceService = custom_service
        else:
            raise ValueError('custom_servicess must contain only subclasses of SpatialReferenceService.')

    # Url Patterns
    query_srid_url = 'rest/spatial-reference/query'

    url_maps = (
        url_map_maker(
            name='atcore_query_spatial_reference',
            url='/'.join([base_url_path, query_srid_url]) if base_url_path else query_srid_url,
            controller=_QuerySpatialReference.as_controller(
                _app=app,
                _persistent_store_name=persistent_store_name,
                _SpatialReferenceService=_SpatialReferenceService
            )
        ),
    )

    return url_maps
