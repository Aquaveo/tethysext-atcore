---
id: reference-permissions-cheatsheet
title: Permissions Cheat Sheet
sidebar_label: Permissions cheat sheet
sidebar_position: 1
---

# Permissions cheat sheet

Quick reference for the role / license matrix and the permissions in each group. The source of truth is [`tethysext/atcore/permissions/app_users.py`](https://github.com/Aquaveo/tethysext-atcore/blob/master/tethysext/atcore/permissions/app_users.py); this page summarizes it.

## Roles

From [`Roles`](../api/services/app_users/roles.mdx):

| Constant | String | Rank |
| --- | --- | --- |
| `ROLES.ORG_USER` | `user_role_org_user` | 100 |
| `ROLES.ORG_REVIEWER` | `user_role_org_reviewer` | 200 |
| `ROLES.ORG_ADMIN` | `user_role_org_admin` | 300 |
| `ROLES.APP_ADMIN` | `user_role_app_admin` | 1000 |
| `ROLES.DEVELOPER` | `user_role_developer` | inf |

## Licenses

From [`Licenses`](../api/services/app_users/licenses.mdx):

| Constant | String | Rank | Can have clients? | Can have consultant? |
| --- | --- | --- | --- | --- |
| `LICENSES.STANDARD` | `standard` | 100 | no | yes |
| `LICENSES.ADVANCED` | `advanced` | 200 | no | yes |
| `LICENSES.PROFESSIONAL` | `professional` | 300 | no | yes |
| `LICENSES.CONSULTANT` | `consultant` | 400 | yes | no |

## Permission groups

[`AppPermissionsManager`](../api/services/app_users/permissions_manager.mdx#apppermissionsmanager) names them with the convention `<license>_<role>_perms`, namespaced to your app:

| Constant | Group name | Notes |
| --- | --- | --- |
| `STD_U_PERMS` | `standard_user_perms` | Standard org user. |
| `STD_R_PERMS` | `standard_reviewer_perms` | Standard org reviewer. |
| `STD_A_PERMS` | `standard_admin_perms` | Standard org admin. |
| `ADV_U_PERMS` | `advanced_user_perms` | |
| `ADV_R_PERMS` | `advanced_reviewer_perms` | |
| `ADV_A_PERMS` | `advanced_admin_perms` | |
| `PRO_U_PERMS` | `professional_user_perms` | |
| `PRO_R_PERMS` | `professional_reviewer_perms` | |
| `PRO_A_PERMS` | `professional_admin_perms` | |
| `CON_U_PERMS` | `consultant_user_perms` | |
| `CON_R_PERMS` | `consultant_reviewer_perms` | |
| `CON_A_PERMS` | `consultant_admin_perms` | Adds `create_organizations`, `edit_organizations`, license-assign perms. |
| `APP_A_PERMS` | `app_admin_perms` | Has _every_ permission. |

Higher-tier groups are supersets of lower-tier groups in the same role column.

## Permissions index

| Permission | Description |
| --- | --- |
| `view_all_resources` | View all resources. |
| `view_resources` | View resources. |
| `view_resource_details` | View details for resources. |
| `create_resource` | Create resources. |
| `edit_resource` | Edit resources. |
| `delete_resource` | Delete resources. |
| `always_delete_resource` | Delete resource even if not editable. |
| `view_users` | View app users. |
| `view_all_users` | View all users. |
| `modify_users` | Edit, delete, create app users. |
| `modify_user_manager` | Modify the manager of a user. |
| `assign_org_user_role` | Assign organization user role. |
| `assign_org_reviewer_role` | Assign organization reviewer role. |
| `assign_org_admin_role` | Assign organization admin role. |
| `assign_app_admin_role` | Assign app admin role. |
| `assign_developer_role` | Assign developer role. |
| `view_organizations` | View organizations. |
| `view_all_organizations` | View any organization. |
| `create_organizations` | Edit, delete, create organizations. |
| `edit_organizations` | Edit organizations. |
| `delete_organizations` | Delete organizations. |
| `modify_organization_members` | Assign / remove members. |
| `assign_any_resource` | Assign any resource to organizations. |
| `assign_any_user` | Assign any user to organizations. |
| `assign_any_organization` | Assign any organization to resources. |
| `assign_standard_license` | Assign standard license. |
| `assign_advanced_license` | Assign advanced license. |
| `assign_professional_license` | Assign professional license. |
| `assign_consultant_license` | Assign consultant license. |
| `assign_any_license` | Assign any license. |
| `remove_layers` | Remove layers from map views. |
| `rename_layers` | Rename layers from map views. |
| `toggle_public_layers` | Toggle layers for public viewing. |
| `use_map_plot` | Use the plotting feature on map views. |
| `use_map_geocode` | Use the geocoding feature on map views. |
| `can_override_user_locks` | Override user locks on workflows. |
| `can_download` | Download layer in map view. |
| `can_export_datatable` | Export data in datatable. |

## Common lookups

```python
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.app_users.licenses import Licenses

pm = AppPermissionsManager('my_first_app')

pm.STANDARD_ADMIN_PERMS
# 'my_first_app:standard_admin_perms'

pm.get_permissions_group_for(role=Roles.ORG_ADMIN, license=Licenses.PROFESSIONAL)
# 'my_first_app:professional_admin_perms'

pm.list(with_namespace=True)
# All enabled, namespaced groups.
```

## See also

- [Permissions](../concepts/permissions.md) — concept-level explanation.
- [`PermissionsGenerator`](../api/permissions/app_users.mdx#permissionsgenerator) — registration entry point.
