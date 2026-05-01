---
id: getting-started-first-app
title: Your First atcore App
sidebar_label: Your first atcore app
sidebar_position: 3
---

# Your first atcore app

This page glues the [installation](./installation.md) and [configuration](./configuration.md) pages into the smallest possible Tethys app that uses atcore. The result: app-user / organization / resource management pages working out of the box.

## Project layout

```
my_first_app/
├── my_first_app/
│   ├── __init__.py
│   ├── app.py
│   ├── controllers.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── projects.py
│   └── templates/
│       └── my_first_app/
│           └── base.html
├── install.yml
└── setup.py / pyproject.toml
```

## Define a `Resource` subclass

```python
# my_first_app/models/projects.py
from sqlalchemy import Column, String
from tethysext.atcore.models.app_users import Resource


class Project(Resource):
    TYPE = 'project'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'

    region = Column(String)

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

## Wire `app.py`

```python
# my_first_app/app.py
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting
from tethysext.atcore.models.app_users import initialize_app_users_db
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.urls import (
    app_users as app_users_urls,
    spatial_reference as sr_urls,
)
from .models.projects import Project


def init_app_users_db(engine, first_time):
    initialize_app_users_db(engine, first_time=first_time)


class MyFirstApp(TethysAppBase):
    name = 'My First App'
    package = 'my_first_app'
    namespace = 'my_first_app'
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'my-first-app'
    color = '#3498db'

    def persistent_store_settings(self):
        return (
            PersistentStoreDatabaseSetting(
                name='app_users_db',
                description='atcore database',
                initializer='my_first_app.app.init_app_users_db',
                spatial=True,
                required=True,
            ),
        )

    def permissions(self):
        pm = AppPermissionsManager(self.namespace)
        return PermissionsGenerator(pm).generate()

    def register_url_maps(self):
        UrlMap = url_map_maker(self.root_url)

        url_maps = [
            UrlMap(
                name='home',
                url='my-first-app',
                controller='my_first_app.controllers.home',
            ),
        ]

        # app_users.urls(custom_resources={...}) registers the user /
        # organization pages and the per-resource CRUD pages in one call.
        # Pass each Resource subclass mapped to its [Manage, Modify(, Details)]
        # controllers, or [] to use the atcore defaults.
        url_maps += list(app_users_urls.urls(
            url_map_maker=UrlMap, app=self,
            persistent_store_name='app_users_db',
            custom_resources={Project: []},  # atcore defaults; pass [Manage, Modify] to override
            base_template='my_first_app/base.html',
        ))

        url_maps += list(sr_urls.urls(
            url_map_maker=UrlMap, app=self,
            persistent_store_name='app_users_db',
        ))

        return tuple(url_maps)
```

:::tip Single-resource shortcut
If you only have one resource type and don't need the user/organization pages, call `resources_urls.urls(..., resource_model=Project)` directly. Prefer `app_users_urls.urls(custom_resources={...})` once you have more than one resource type or an `Organization` subclass — you won't have to rewire later.
:::

## Bootstrap the database

```bash
tethys syncstores my_first_app
```

This calls your initializer, which calls [`initialize_app_users_db`](../api/models/app_users/initializer.mdx), which creates the atcore tables and seeds the staff/developer user.

## Try it out

Start Tethys and visit:

- `/apps/my-first-app/users/` — `ManageUsers` page (named `app_users_manage_users`).
- `/apps/my-first-app/organizations/` — `ManageOrganizations`.
- `/apps/my-first-app/projects/` — `ManageResources` for `Project`.

The exact paths come from your `root_url` plus the URL prefix each atcore `urls(...)` factory adds.

## Next

- Add a custom workflow: [Build a Resource Workflow](../how-to/build-a-resource-workflow.md).
- Add a map page for your resource: [Customize a Map View](../how-to/customize-a-map-view.md).
- Read the end-to-end [walkthrough](../tutorials/walkthrough.md).
