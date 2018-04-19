"""
********************************************************************************
* Name: permissions
* Author: nswain
* Created On: April 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""


def mock_has_permission_false(*args, **kwargs):
    return False


def mock_has_permission_true(*args, **kwargs):
    return True


def mock_has_permission_assignable_roles(request, permission, *args, **kwargs):
    return permission in ['assign_org_users_role', 'assign_org_admin_role']
