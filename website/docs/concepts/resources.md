---
id: concepts-resources
title: Resources
sidebar_label: Resources
sidebar_position: 3
---

# Resources

A `Resource` is the central domain object in atcore. Subclass it once per "thing the user manages" (a project, scenario, model run, asset). Atcore's controllers and URL helpers do the CRUD wiring.

## The base class

[`Resource`](../api/models/app_users/resource.mdx#resource) is a SQLAlchemy model that composes four mixins:

- [`StatusMixin`](../api/mixins/status_mixin.mdx) — keyed status dictionary (`get_status` / `set_status`), with constants like `STATUS_PENDING`, `STATUS_PROCESSING`, `STATUS_SUCCESS`, `STATUS_ERROR`.
- [`AttributesMixin`](../api/mixins/attributes_mixin.mdx) — free-form JSON attributes via `get_attribute` / `set_attribute`.
- [`UserLockMixin`](../api/mixins/user_lock_mixin.mdx) — soft lock so only one user can edit a resource at a time.
- [`SerializeMixin`](../api/mixins/serialize_mixin.mdx) — `serialize()` for dict / JSON responses.

Columns include `id` (UUID), `name`, `description`, `type`, `date_created`, `created_by`, `status`, and `public`. Resources belong to one or more `Organization`s and can be nested via `parents` / `children`.

## Subclassing

Subclass `Resource` and set the polymorphic identity:

```python
# example — myapp_adapter/resources/project.py
from tethysext.atcore.models.app_users import Resource


class Project(Resource):
    TYPE = 'project'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

`Resource.SLUG` is a `classproperty` derived from `DISPLAY_TYPE_PLURAL`, so the example above produces URL maps prefixed with `projects_`.

## SpatialResource vs. raw geometry columns

If your resource has a single rectangular geographic extent, subclass [`SpatialResource`](../api/models/app_users/spatial_resource.mdx). It adds a PostGIS `extent` column and `set_extent` / `get_extent` helpers that accept WKT, GeoJSON, or a Python dict (with an SRID).

For richer geometry needs — arbitrary polygon areas-of-interest, point gauge locations, multiple geometries — stay on plain `Resource` and add a geoalchemy2 `Geometry` column directly:

```python
from geoalchemy2 import Geometry
from sqlalchemy import Column

class Project(Resource):
    TYPE = 'project'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    area_of_interest = Column(Geometry('POLYGON', 4326))
```

`SpatialResource` is convenient when all you need is an extent for the resource list / map preview. Apps that JOIN against the geometry, store multiple geometries, or use non-rectangular shapes inherit from `Resource` directly and add their own column.

## Hard columns vs. soft attributes

The split:

- Hard SQL columns for fields you filter, JOIN, or query against — geometry, foreign keys, anything the database needs to reason about. These go on the `Resource` subclass as `Column(...)`.
- Soft attributes via the inherited `_attributes` JSON blob for everything else — sparse per-resource configuration, status keys, file paths, runtime state. Use `set_attribute('foo', value)` and `get_attribute('foo', default)`.

```python
# example — controller code that uses both styles
project.area_of_interest          # hard column — JOIN-friendly
project.set_attribute('database_id', uuid.uuid4().hex)
project.set_attribute('input_files', ['boundary.shp', 'soils.tif'])

db_id = project.get_attribute('database_id')
```

Things like `database_id`, `srid`, `input_file`, `dataset_type`, `extent_geometry` are typically attributes, not columns. The benefit: you can add new state to a resource without writing a migration. The cost: no `WHERE database_id = ?` in SQL. When that becomes a real need, promote the field to a column and write the migration.

## Cross-cutting behavior with mixins

When several `Resource` subclasses share behavior — a parent-child link, an SRID attribute, an input-file convention — don't fatten the base class. Write a mixin and compose it onto each subclass that needs it. Atcore itself uses this pattern (`StatusMixin`, `AttributesMixin`, `UserLockMixin`); apps extend it:

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

Mixins of this shape don't add columns; they expose typed accessors over the JSON `_attributes` blob. A mixin that does need a column (e.g., a `LinkMixin` using the `parents`/`children` association table) either declares the column directly or relies on inherited columns from `Resource`.

## Lifecycle

The default `Resource` lifecycle, as exercised by atcore controllers and the condor workflow helpers:

1. Create — `ModifyResource` creates the row, runs validation, and sets `status` to `STATUS_PENDING`.
2. Initialize — long-running setup runs as a Condor job (see [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx)). The job posts back to the resource's status using one or more status keys.
3. Available — once the initialization keys all resolve to an OK status (`STATUS_AVAILABLE`, `STATUS_SUCCESS`, etc.), the resource is usable.
4. Edit / use — `ResourceDetails`, `MapView`, and any custom workflows act on the resource.
5. Delete — `ModifyResource` flips `status` to `STATUS_DELETING` and removes the row plus any side effects.

`StatusMixin` exposes `OK_STATUSES`, `ERROR_STATUSES`, `WORKING_STATUSES`, and `COMPLETE_STATUSES` for grouping.

:::tip Async deletion for resources with heavy artifacts
Resources that own large file databases, GeoServer layers, or Condor working directories should override `ManageResources._handle_delete` to flip the status to `STATUS_DELETING` and spawn a daemon `Thread` for the cleanup. Synchronous deletion blocks the request and can time out on big projects.
:::

## Wiring resource URLs

Two equivalent ways to register CRUD pages for a resource subclass.

Single resource, dedicated call — useful when the resource pages *are* the app:

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

Multiple resources, consolidated call — preferred when you have several resource types, because it produces the app-user pages and per-resource pages in one shot:

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

`custom_resources` accepts a dict of `{ResourceClass: [Manage, Modify(, Details)]}`. `app_users.urls(...)` calls `resources.urls(...)` once per entry, so app-user, organization, and resource URLs are registered together.

Either way, the URLs produced (with `Project.SLUG` substituted):

- `<slug>_manage_resources`
- `<slug>_new_resource`
- `<slug>_edit_resource`
- `<slug>_resource_details`
- `<slug>_resource_status`
- `<slug>_resource_status_list`

## Next

- [Resource Workflows](./resource-workflows.md) — multi-step processes attached to a resource.
- [Controllers](./controllers.md) — subclassing `ManageResources`, `ModifyResource`, and `TabbedResourceDetails`.
- [File Database](./file-database.md) — how a resource owns on-disk artifacts.
