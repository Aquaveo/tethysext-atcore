import inspect
from tethys_sdk.base import TethysController
from tethysext.atcore.controllers.app_users import ManageUsers
from tethysext.atcore.controllers.app_users import ModifyUser
from tethysext.atcore.controllers.app_users import AddExistingUser


def urls(url_map_maker, *args, **kwargs):
    """
    Generate UrlMap objects for app_users extension. To link to pages provided by the app_users extension use the name of the url with your app namespace:  # noqa: F401

    ::

        {% url 'my_first_app:add_user %}
        {% url 'my_first_app:edit_user, user_id=user.id %}

    Args:
        root_url(str): value of root_url attribute of app class.
        args: Any number of TethysController subclasses to override default controller classes.
        kwargs: Any number of keyword options.

    Keyword Options:
        base_url_path(str, optional): url path to prepend to all app_user urls (e.g.: 'foo/bar').

    Url Map Names:
        manage_users
        add_user
        edit_user <user_id>
        add_existing_user

    Returns:
        tuple: UrlMap objects for the app_users extension.
    """
    # Get kwargs
    base_url_path = kwargs.get('base_url_path', '')

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

    # Validate controller classes
    for arg in args:
        if not inspect.isclass(arg) or not issubclass(arg, TethysController):
            raise ValueError('Args must be valid TethysController sub classes.')
        elif issubclass(arg, ManageUsers):
            _ManageUsers = arg
        elif issubclass(arg, ModifyUser):
            _ModifyUser = arg
        elif issubclass(arg, AddExistingUser):
            _AddExistingUser = arg

    url_maps = (
        url_map_maker(
            name='manage_users',
            url='/'.join([base_url_path, 'users']) if base_url_path else 'users',
            controller=_ManageUsers.as_controller()
        ),
        url_map_maker(
            name='add_user',
            url='/'.join([base_url_path, 'users/add']) if base_url_path else 'users/add',
            controller=_ModifyUser.as_controller()
        ),
        url_map_maker(
            name='edit_user',
            url='/'.join([base_url_path, 'users/{user_id}/edit']) if base_url_path else 'users/{user_id}/edit',
            controller=_ModifyUser.as_controller()
        ),
        url_map_maker(
            name='add_existing_user',
            url='/'.join([base_url_path, 'users/add-existing']) if base_url_path else 'users/add-existing',
            controller=_AddExistingUser.as_controller()
        ),
    )

    return url_maps
