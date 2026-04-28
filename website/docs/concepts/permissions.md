---
id: concepts-permissions
title: Permissions
sidebar_label: Permissions
sidebar_position: 8
---

# Permissions

atcore generates a permission matrix from two axes — the user's [role](../api/services/app_users/roles.mdx) and the licenses of the [organizations](./app-users.md) they belong to. The result is a fixed set of permission groups that you wire into Tethys's permission system.

## The matrix

Roles ([`Roles`](../api/services/app_users/roles.mdx)):

| Role | Description |
| --- | --- |
| `ORG_USER` | Member of an organization. |
| `ORG_REVIEWER` | Member with review authority. |
| `ORG_ADMIN` | Manages members and resources in their org. |
| `APP_ADMIN` | Manages everything in the app. |
| `DEVELOPER` | Out-ranks all roles (used for staff). |

Licenses ([`Licenses`](../api/services/app_users/licenses.mdx)):

| License | Notes |
| --- | --- |
| `STANDARD` | |
| `ADVANCED` | |
| `PROFESSIONAL` | |
| `CONSULTANT` | Can have client organizations. |

The cross-product produces 12 organizational permission groups (license × {`USER`, `REVIEWER`, `ADMIN`}) plus the global `APP_A_PERMS`. Each group is namespaced to your app — e.g. `my_first_app:standard_admin_perms`.

## AppPermissionsManager

Use [`AppPermissionsManager`](../api/services/app_users/permissions_manager.mdx#apppermissionsmanager) to look up the permission group for a user. It's instantiated with your app namespace:

```python
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager

pm = AppPermissionsManager('my_first_app')
group = pm.get_permissions_group_for(role=Roles.ORG_ADMIN, license=Licenses.STANDARD)
# 'my_first_app:standard_admin_perms'
```

Common methods:

- `list(with_namespace=False)` — all enabled groups.
- `get_permissions_group_for(role, license=...)` — group name for a (role, license) pair.
- `get_has_role_permission_for(role, license=...)` — name of the per-role flag permission.

## Generating permissions

Register the permission groups with Tethys by hooking [`PermissionsGenerator`](../api/permissions/app_users.mdx#permissionsgenerator) into your app's `permissions()` method:

```python
# example — app.py
from tethys_sdk.base import TethysAppBase
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class MyFirstApp(TethysAppBase):
    name = 'My First App'

    def permissions(self):
        pm = AppPermissionsManager(self.namespace)
        gen = PermissionsGenerator(pm)
        # Optional: add app-specific permissions to a group
        # gen.add_permissions_for(pm.STD_A_PERMS, [my_extra_permission])
        return gen.generate()
```

The generator emits Tethys `PermissionGroup` instances with a curated set of permissions per group. The full breakdown is in [`permissions/app_users.py`](https://github.com/Aquaveo/tethysext-atcore/blob/master/tethysext/atcore/permissions/app_users.py); a quick view is on the [Permissions cheat sheet](../reference/permissions-cheatsheet.md).

## Built-in permissions

Permissions defined by `PermissionsGenerator` cluster into five buckets:

- **Resource management** — `view_all_resources`, `view_resources`, `view_resource_details`, `create_resource`, `edit_resource`, `delete_resource`, `always_delete_resource`.
- **User management** — `view_users`, `view_all_users`, `modify_users`, `modify_user_manager`, plus role-assignment perms (`assign_org_user_role`, `assign_org_admin_role`, `assign_app_admin_role`, `assign_developer_role`, etc.).
- **Organization management** — `view_organizations`, `view_all_organizations`, `create_organizations`, `edit_organizations`, `delete_organizations`, `modify_organization_members`.
- **Assignment** — `assign_any_resource`, `assign_any_user`, `assign_any_organization`, plus license-assignment perms (`assign_standard_license`, `assign_advanced_license`, etc.).
- **Map view** — `remove_layers`, `rename_layers`, `toggle_public_layers`, `use_map_plot`, `use_map_geocode`, `can_download`, `can_export_datatable`. Plus `can_override_user_locks` for workflow lock overrides.

## Checking permissions in code

Use Tethys's standard permission helpers — atcore's groups are normal Tethys groups:

```python
from tethys_sdk.permissions import has_permission, permission_required

if has_permission(request, 'edit_resource'):
    ...

@permission_required('delete_resource')
def my_view(self, request, ...):
    ...
```

For class-based controllers, atcore's `ResourceView` already runs the auth/active-user checks — apply `@permission_required` (or your own check) to the specific method or action.
