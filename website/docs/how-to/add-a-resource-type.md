---
id: how-to-add-a-resource-type
title: Add a Resource Type
sidebar_label: Add a resource type
sidebar_position: 1
---

# Add a resource type

This recipe walks through subclassing `Resource` for a custom domain type and wiring its CRUD pages.

## 1. Subclass `Resource`

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

`Resource.SLUG` (a `classproperty`) auto-derives `'projects'` from `DISPLAY_TYPE_PLURAL`. URL maps for this resource will be prefixed `projects_`.

If you need a geographic extent, subclass [`SpatialResource`](../api/models/app_users/spatial_resource.mdx) instead and set the polymorphic identity to your own type.

## 2. Make sure the table is created

The `Project` row lives in the same `app_users_resources` table as `Resource` (single-table inheritance). Calling [`initialize_app_users_db`](../api/models/app_users/initializer.mdx) is enough — no migration required if you add columns via single-table inheritance, since `region` becomes a nullable column on the shared table.

If you add columns that must be present, run a one-off migration that adds the column.

## 3. Register the resource URLs

```python
# my_first_app/app.py — register_url_maps
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethysext.atcore.urls import resources as resources_urls
from .models.projects import Project


class MyFirstApp(TethysAppBase):
    name = 'My First App'
    package = 'my_first_app'
    namespace = 'my_first_app'

    def register_url_maps(self):
        UrlMap = url_map_maker(self.root_url)
        url_maps = [...]

        url_maps += list(resources_urls.urls(
            url_map_maker=UrlMap,
            app=self,
            persistent_store_name='app_users_db',
            resource_model=Project,
            base_template='my_first_app/base.html',
        ))

        return tuple(url_maps)
```

You'll get six URL maps:

- `projects_manage_resources`
- `projects_new_resource`
- `projects_edit_resource`
- `projects_resource_details`
- `projects_resource_status`
- `projects_resource_status_list`

## 4. (Optional) Override controllers

If you need different behavior on the management pages, subclass any of [`ManageResources`](../api/controllers/app_users/manage_resources.mdx), [`ModifyResource`](../api/controllers/app_users/modify_resource.mdx), [`ResourceDetails`](../api/controllers/app_users/resource_details.mdx), or [`ResourceStatus`](../api/controllers/app_users/resource_status.mdx) and pass them via `custom_controllers`:

```python
url_maps += list(resources_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='app_users_db',
    resource_model=Project,
    custom_controllers=[ProjectModifyResource, ProjectResourceDetails],
))
```

The factory checks each entry against `ManageResources`, `ModifyResource`, `ResourceDetails`, and `ResourceStatus` and substitutes the right one.

## 5. Link to the page

```html
<a href="{% url 'my_first_app:projects_manage_resources' %}">My Projects</a>
```

The URL name is namespaced to your app's `namespace` setting.

:::tip
Need attributes that vary per project but don't deserve a column? Use `project.set_attribute('foo', value)` (`AttributesMixin`) instead of adding a column. Stored as JSON in `_attributes`.
:::
