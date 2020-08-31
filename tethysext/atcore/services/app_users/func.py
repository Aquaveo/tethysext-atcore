"""
********************************************************************************
* Name: func
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


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
