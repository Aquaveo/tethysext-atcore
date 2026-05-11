---
id: concepts-app-users
title: App Users and Organizations
sidebar_label: App Users
sidebar_position: 2
---

# App users and organizations

The `app_users` system is atcore's identity model. It sits next to Django's auth users and adds an app-scoped layer for membership, roles, and licensing.

## The core trio

The models live under [`tethysext.atcore.models.app_users`](../api/models/app_users/index.mdx):

- [`AppUser`](../api/models/app_users/app_user.mdx#appuser) — one row per app-aware user. Each `AppUser.username` maps to a Django user. Stores a `role` and an `is_active` flag, plus a list of `organizations` and `settings`.
- [`Organization`](../api/models/app_users/organization.mdx) — a group that owns resources. Has a `license`, `members` (`AppUser`s), and `resources`.
- [`Resource`](../api/models/app_users/resource.mdx#resource) — a domain object owned by one or more organizations. See [Resources](./resources.md).

These three share `AppUsersBase` ([`models.app_users.base`](../api/models/app_users/base.mdx)), a SQLAlchemy declarative base that you bind to your app's app-users persistent store.

## Roles and licenses

Roles ([`Roles`](../api/services/app_users/roles.mdx)) are user-level — what is this person allowed to do?

```python
from tethysext.atcore.services.app_users.roles import Roles

Roles.ORG_USER       # 'user_role_org_user'
Roles.ORG_REVIEWER   # 'user_role_org_reviewer'
Roles.ORG_ADMIN      # 'user_role_org_admin'
Roles.APP_ADMIN      # 'user_role_app_admin'
Roles.DEVELOPER      # 'user_role_developer'
```

Licenses ([`Licenses`](../api/services/app_users/licenses.mdx)) are organization-level — what tier of features did this organization buy?

```python
from tethysext.atcore.services.app_users.licenses import Licenses

Licenses.STANDARD
Licenses.ADVANCED
Licenses.PROFESSIONAL
Licenses.CONSULTANT
```

A user's effective permissions are the cross-product of their role and the licenses of the organizations they belong to. The [`AppPermissionsManager`](../api/services/app_users/permissions_manager.mdx#apppermissionsmanager) computes the permission-group name for any (role, license) pair, namespaced to your app.

See the [Permissions concept page](./permissions.md) for the full matrix.

## Initializing the database

Call [`initialize_app_users_db`](../api/models/app_users/initializer.mdx) from your Tethys app's `persistent_store_initializer` to create the tables and seed the developer/staff user:

```python
# example — app.py
from tethysext.atcore.models.app_users import initialize_app_users_db

def init_app_users_db(engine, first_time):
    initialize_app_users_db(engine, first_time=first_time)
```

If you've subclassed `AppUser`, pass it via `app_user_model=MyAppUser`.

## Wiring the URLs

Register the app-user CRUD pages from [`tethysext.atcore.urls.app_users`](../api/urls/app_users.mdx):

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import app_users as app_users_urls

url_maps = app_users_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='app_users_db',
    base_template='my_first_app/base.html',
)
```

This emits URL maps like `app_users_manage_users`, `app_users_add_user`, `app_users_manage_organizations`, etc. — the full list is in the docstring at [`urls.app_users`](../api/urls/app_users.mdx).

## Subclassing models

You can extend `AppUser`, `Organization`, and `Resource` and pass your subclasses into `urls(..., custom_models=[MyAppUser, MyOrganization])`. The matching `Modify*` and `Manage*` controllers will pick them up.

:::tip
For most apps the right level of customization is **Resource** (custom fields, polymorphic types). Subclassing `AppUser` or `Organization` is rarer — the defaults already cover username/role/membership.
:::
