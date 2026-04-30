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
# example — myapp_adapter/resources/project.py
from tethysext.atcore.models.app_users import Resource


class Project(Resource):
    TYPE = 'project'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

`Resource.SLUG` (a `classproperty`) auto-derives a URL slug from `DISPLAY_TYPE_PLURAL`, so the example above produces URL maps prefixed with `projects_`.

## SpatialResource vs. raw geometry columns

If your resource has a single rectangular geographic extent, subclass [`SpatialResource`](../api/models/app_users/spatial_resource.mdx) instead. It adds a PostGIS `extent` column and `set_extent` / `get_extent` helpers that accept WKT, GeoJSON, or a Python dict (with an SRID).

For richer geometry needs (an arbitrary polygon area-of-interest, point gauge locations, etc.), you can also stay on plain `Resource` and add a geoalchemy2 `Geometry` column directly:

```python
from geoalchemy2 import Geometry
from sqlalchemy import Column

class Project(Resource):
    TYPE = 'project'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    area_of_interest = Column(Geometry('POLYGON', 4326))
```

`SpatialResource` is convenient when you just need an extent for the resource list / map preview. Apps that need to JOIN against the geometry, store multiple geometries, or use non-rectangular shapes typically inherit from `Resource` directly and add their own column — both production apps in this repo (agwa, tribs) take that path.

## Hard columns vs. soft attributes

Production atcore apps follow a deliberate split:

- **Hard SQL columns** for fields you filter, JOIN, or query against — geometry, foreign keys, things the database needs to reason about. These go on the `Resource` subclass as `Column(...)`.
- **Soft attributes** stored via the inherited `_attributes` JSON blob for everything else — sparse per-resource configuration, status keys, file paths, runtime state. Use `set_attribute('foo', value)` and `get_attribute('foo', default)`.

```python
# example — controller code that uses both styles
project.area_of_interest          # hard column — JOIN-friendly
project.set_attribute('database_id', uuid.uuid4().hex)
project.set_attribute('input_files', ['boundary.shp', 'soils.tif'])

db_id = project.get_attribute('database_id')
```

Real apps store things like `database_id`, `srid`, `input_file`, `dataset_type`, `extent_geometry` as attributes — none of them are columns. The benefit: you can add a new piece of state to a resource without writing a migration. The trade-off: you can't `WHERE database_id = ?` in SQL — but you almost never need to for JSON-bag fields. When you find yourself needing to, *that's* when you promote the field to a real column with a migration.

## Cross-cutting behavior with mixins

When several `Resource` subclasses share the same behavior (a parent-child link, an SRID attribute, an input-file convention), don't fatten the base class — write a mixin and compose it onto each `Resource` subclass that needs it. Atcore's own design uses this idiom (`StatusMixin`, `AttributesMixin`, `UserLockMixin`), and production apps extend it:

```python
# example — myapp_adapter/resources/mixins/srid_attr_mixin.py
class SridAttrMixin:
    """Adds an `srid` property backed by the AttributesMixin store."""
    SRID_KEY = 'srid'

    @property
    def srid(self):
        return self.get_attribute(self.SRID_KEY)

    @srid.setter
    def srid(self, value):
        self.set_attribute(self.SRID_KEY, int(value))


# myapp_adapter/resources/scenario.py
from tethysext.atcore.models.app_users import Resource
from .mixins.srid_attr_mixin import SridAttrMixin


class Scenario(Resource, SridAttrMixin):
    TYPE = 'scenario'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

Mixins of this shape don't add columns; they just expose typed accessors over the JSON `_attributes` blob. When a mixin *does* need a column (e.g., a `LinkMixin` that uses the `parents`/`children` association table), it either declares the column directly or relies on inherited columns from `Resource`.

## Lifecycle

The default `Resource` lifecycle as exercised by atcore controllers and the condor workflow helpers:

1. **Create** — `ModifyResource` controller creates the row, runs validation, and sets `status` to `STATUS_PENDING`.
2. **Initialize** — long-running setup runs as a Condor job (see [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx)). The job posts back to the resource's status using one or more status keys.
3. **Available** — once the initialization keys all resolve to an OK status (`STATUS_AVAILABLE`, `STATUS_SUCCESS`, etc.), the resource is usable.
4. **Edit / use** — `ResourceDetails`, `MapView`, and any custom workflows act on the resource.
5. **Delete** — `ModifyResource` flips `status` to `STATUS_DELETING` and removes the row + any side effects.

The `OK_STATUSES`, `ERROR_STATUSES`, `WORKING_STATUSES`, and `COMPLETE_STATUSES` lists on `StatusMixin` are the canonical buckets.

:::tip Async deletion for resources with heavy artifacts
Resources that own large file databases, GeoServer layers, or Condor working directories should override `ManageResources._handle_delete` to flip the status to `STATUS_DELETING` and spawn a daemon `Thread` for the cleanup. Synchronous deletion blocks the request and times out on big projects. Both production apps in this repo do this — see [`ManageResourceDeleteMixin`](https://github.com/Aquaveo/tethysext-atcore/tree/master/apps/tethysapp-tribs) for an example pattern.
:::

## Wiring resource URLs

Two equivalent ways to register CRUD pages for a resource subclass.

**Single resource, dedicated call** — useful when you want the resource pages to be the entire app:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import resources as resources_urls
from myapp_adapter.resources.project import Project

url_maps = list(resources_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='primary_db',
    resource_model=Project,
    base_template='myapp/base.html',
))
```

**Multiple resources, consolidated call** — preferred for apps with several resource types, because it produces the app-user pages and per-resource pages in one shot:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import app_users as app_users_urls
from myapp_adapter.resources.project import Project
from myapp_adapter.resources.scenario import Scenario
from myapp.controllers.resources.manage_projects import ManageProjects, ModifyProject
from myapp.controllers.resources.manage_scenarios import ManageScenarios, ModifyScenario

url_maps = list(app_users_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='primary_db',
    custom_resources={
        Project: [ManageProjects, ModifyProject],
        Scenario: [ManageScenarios, ModifyScenario],
    },
    custom_models=[MyAppUser, MyOrganization],
    custom_permissions_manager=MyPermissionsManager,
    base_template='myapp/base.html',
))
```

`custom_resources` accepts a dict of `{ResourceClass: [Manage, Modify(, Details)]}`. Internally `app_users.urls(...)` calls `resources.urls(...)` once per entry, so you get the app-user, organization, and resource URLs registered together.

Either way, the URLs produced (substituting `Project.SLUG`):

- `<slug>_manage_resources`
- `<slug>_new_resource`
- `<slug>_edit_resource`
- `<slug>_resource_details`
- `<slug>_resource_status`
- `<slug>_resource_status_list`

## Next

- [Resource Workflows](./resource-workflows.md) — multi-step processes attached to a resource.
- [Controllers](./controllers.md) — how `ManageResources`, `ModifyResource`, and `TabbedResourceDetails` are subclassed.
- [File Database](./file-database.md) — how a resource owns on-disk artifacts.
