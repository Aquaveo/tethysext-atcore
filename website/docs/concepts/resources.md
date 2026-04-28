---
id: concepts-resources
title: Resources
sidebar_label: Resources
sidebar_position: 3
---

# Resources

A `Resource` is the central domain object in atcore. Most apps subclass it once per "thing the user manages" — a project, scenario, model run, asset — and atcore's controllers and URL helpers do the CRUD wiring.

## The base class

[`Resource`](../api/models/app_users/resource.mdx#resource) is a SQLAlchemy model that composes four mixins:

- [`StatusMixin`](../api/mixins/status_mixin.mdx) — keyed status dictionary (`get_status` / `set_status`), with constants like `STATUS_PENDING`, `STATUS_PROCESSING`, `STATUS_SUCCESS`, `STATUS_ERROR`.
- [`AttributesMixin`](../api/mixins/attributes_mixin.mdx) — JSON-serialized free-form attributes via `get_attribute` / `set_attribute`.
- [`UserLockMixin`](../api/mixins/user_lock_mixin.mdx) — soft locking so only one user can edit a resource at a time.
- [`SerializeMixin`](../api/mixins/serialize_mixin.mdx) — `serialize()` for dict / JSON responses.

Stored columns include `id` (UUID), `name`, `description`, `type`, `date_created`, `created_by`, `status`, and `public`. Resources belong to one or more `Organization`s and can be nested via `parents` / `children`.

## Subclassing

To define a new resource type, subclass `Resource` and set the polymorphic identity:

```python
# example — models/my_resource.py
from sqlalchemy import Column, String
from tethysext.atcore.models.app_users import Resource


class MyProject(Resource):
    TYPE = 'my_project'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'

    region = Column(String)

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

`Resource.SLUG` (a `classproperty`) auto-derives a URL slug from `DISPLAY_TYPE_PLURAL`, so the example above produces URL maps prefixed with `projects_`.

## SpatialResource

If your resource has a geographic extent, subclass [`SpatialResource`](../api/models/app_users/spatial_resource.mdx) instead. It adds a PostGIS `extent` column and `set_extent` / `get_extent` helpers that accept WKT, GeoJSON, or a Python dict (with an SRID).

## Lifecycle

The default `Resource` lifecycle as exercised by atcore controllers and the condor workflow helpers:

1. **Create** — `ModifyResource` controller creates the row, runs validation, and sets `status` to `STATUS_PENDING`.
2. **Initialize** — long-running setup runs as a Condor job (see [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx)). The job posts back to the resource's status using one or more status keys.
3. **Available** — once the initialization keys all resolve to an OK status (`STATUS_AVAILABLE`, `STATUS_SUCCESS`, etc.), the resource is usable.
4. **Edit / use** — `ResourceDetails`, `MapView`, and any custom workflows act on the resource.
5. **Delete** — `ModifyResource` flips `status` to `STATUS_DELETING` and removes the row + any side effects.

The `OK_STATUSES`, `ERROR_STATUSES`, `WORKING_STATUSES`, and `COMPLETE_STATUSES` lists on `StatusMixin` are the canonical buckets.

## Wiring resource URLs

Use [`tethysext.atcore.urls.resources.urls`](../api/urls/resources.mdx) to register the management pages for each resource subclass:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import resources as resources_urls
from .models.my_resource import MyProject

url_maps = resources_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='app_users_db',
    resource_model=MyProject,
    base_template='my_first_app/base.html',
)
```

This produces (substituting `MyProject.SLUG`):

- `<slug>_manage_resources`
- `<slug>_new_resource`
- `<slug>_edit_resource`
- `<slug>_resource_details`
- `<slug>_resource_status`
- `<slug>_resource_status_list`

Override the default controllers by passing subclasses via `custom_controllers=[MyResourceDetails]`.

## Attributes vs columns

Use real columns for fields you query against. Use `set_attribute('foo', value)` for sparse, varied bag-of-properties data — internally stored as JSON in the `_attributes` column. The condor workflow integration uses attributes for things like `database_id` and `scenario_id`.
