---
id: concepts-services
title: Services
sidebar_label: Services
sidebar_position: 6
---

# Services

The `services` package holds atcore's stateful helpers — things that aren't models or controllers but back the behavior of both.

## Spatial managers

[`BaseSpatialManager`](../api/services/base_spatial_manager.mdx) is the abstract parent for managers that talk to GeoServer. Concrete managers:

- [`ModelDBSpatialManager`](../api/services/model_db_spatial_manager.mdx) — for layers tied to a model database.
- [`ModelFileDBSpatialManager`](../api/services/model_file_db_spatial_manager.mdx) — for layers tied to a model + file database.
- [`ResourceSpatialManager`](../api/services/resource_spatial_manager.mdx) — for layers tied to a `Resource`.

A spatial manager owns the GeoServer workspace name (`WORKSPACE`), URI, cluster ports, SLD path, and the SQL/PostGIS path. Subclass it and override what you need:

```python
# example — services/my_spatial_manager.py
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager


class MySpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'
    URI = 'http://app.aquaveo.com/my_first_app'
```

The `reload_config` decorator from [`services.base_spatial_manager`](../api/services/base_spatial_manager.mdx) refreshes the GeoServer cluster after mutating ops.

## Map manager

[`MapManagerBase`](../api/services/map_manager.mdx) builds Tethys `MapView` configurations for `MapView` controllers. Subclass it and implement the abstract `compose_map(self, request, *args, **kwargs)` to return a `(MapView, extent)` pair (where `extent` is a 4-list of floats).

## Model database

[`ModelDatabase`](../api/services/model_database.mdx) and [`ModelDatabaseConnection`](../api/services/model_database_connection.mdx) wrap a per-resource Postgres database. The base classes are [`ModelDatabaseBase`](../api/services/model_database_base.mdx) and [`ModelDatabaseConnectionBase`](../api/services/model_database_connection_base.mdx). The file-backed cousin is [`ModelFileDatabase`](../api/services/model_file_database.mdx) / [`ModelFileDatabaseConnection`](../api/services/model_file_database_connection.mdx).

Use a `ModelDatabase` when each resource needs an isolated Postgres database (e.g., one DB per scenario / project). It load-balances across multiple Tethys persistent-store DB connections if your app declares more than one.

### The connection-pool pattern

`ModelDatabase` doesn't operate against a single named database — it dynamically creates one PostGIS database per resource by selecting from a pool of `PersistentStoreConnectionSetting` entries declared by the app:

```python
def persistent_store_settings(self):
    return (
        PersistentStoreDatabaseSetting(
            name='primary_db', initializer='myapp.models.init_primary_db',
            spatial=True, required=True,
        ),
        PersistentStoreConnectionSetting(name='model_db_1', required=True),
        PersistentStoreConnectionSetting(name='model_db_2', required=True),
        PersistentStoreConnectionSetting(name='model_db_3', required=True),
    )
```

Each `model_db_N` is a *connection* to a Postgres server, not a database. When `ModelDatabase(app=app, database_id=...).initialize()` runs, atcore picks the least-loaded connection and creates a fresh database on it named after `database_id`. The mapping from resource → server is balanced across the declared connections, so you can scale by adding more `model_db_N` entries.

Resources record their assigned `database_id` as an attribute (`resource.set_attribute('database_id', uuid_hex)`), and the `MapManager` resolves it back to a `ModelDatabase` when rendering layers.

### `ModelDatabase` vs. `FileDatabase`

| | `ModelDatabase` | `FileDatabase` |
| --- | --- | --- |
| Storage | Per-resource PostGIS database | Per-resource directory on disk |
| Best for | Spatial layers published to GeoServer; SQL-queryable per-resource state | Bulk input/output files (rasters, archives, model output) |
| Layer publishing | `ModelDBSpatialManager` registers the DB as a GeoServer datastore | `BaseSpatialManager` reads files and publishes layers individually |
| Cleanup | Drop the database when the resource is deleted | Drop the directory tree |
| Scaling | Add more `PersistentStoreConnectionSetting` entries | Mount more disk |

Production apps mix both: an analysis app that produces maps from geospatial inputs uses `ModelDatabase` for the per-resource layer store and `FileDatabase` for the input rasters that fed it.

## Permissions manager

[`AppPermissionsManager`](../api/services/app_users/permissions_manager.mdx#apppermissionsmanager) is the runtime helper for atcore's role/license matrix. See the [Permissions concept page](./permissions.md) and the [Permissions cheat sheet](../reference/permissions-cheatsheet.md).

## Workflow managers

For long-running workflow steps, atcore submits HTCondor workflows:

- [`BaseWorkflowManager`](../api/services/workflow_manager/base_workflow_manager.mdx) — base.
- [`ResourceWorkflowCondorJobManager`](../api/services/workflow_manager/condor_workflow_manager.mdx) — submits Condor workflows for a `ResourceWorkflowStep` and writes status back to the resource.
- [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx) — submits the resource initialization workflow that runs after a `Resource` is created.

See [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md) for an end-to-end example.

## File database client

[`FileDatabaseClient`](../api/services/file_database.mdx#filedatabaseclient) and [`FileCollectionClient`](../api/services/file_database.mdx#filecollectionclient) wrap the [`FileDatabase`](../api/models/file_database/file_database-module.mdx) model. See [File Database](./file-database.md).

## Spatial reference

[`SpatialReferenceService`](../api/services/spatial_reference.mdx) queries the PostGIS `spatial_ref_sys` table by SRID or name. It backs the `QuerySpatialReference` REST controller and the [`SpatialReferenceSelect`](./gizmos.md) gizmo.

## Pagination and color ramps

- [`paginate`](../api/services/paginate.mdx) — slice a list of records into pages with metadata.
- [`color_ramps`](../api/services/color_ramps.mdx) — predefined color ramps for thematic map styling.

## Resource workflow helpers

- [`services.resource_workflows.decorators.workflow_step_controller`](../api/services/resource_workflows/decorators.mdx) — view decorator for workflow step controllers.
- [`services.resource_workflows.helpers`](../api/services/resource_workflows/helpers.mdx) — shared helpers used by workflow views.
