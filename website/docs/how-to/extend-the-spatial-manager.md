---
id: how-to-extend-the-spatial-manager
title: Extend the Spatial Manager
sidebar_label: Extend the spatial manager
sidebar_position: 6
---

# Extend the spatial manager

The spatial manager is the GeoServer-facing helper for atcore's map views. Subclass [`BaseSpatialManager`](../api/services/base_spatial_manager.mdx) (or one of its more specific subclasses) and customize the workspace, URI, SLD path, and any layer publishing operations.

## Pick the right base class

| Use this | When |
| --- | --- |
| [`BaseSpatialManager`](../api/services/base_spatial_manager.mdx) | You're rolling your own without atcore's model/file database integration. |
| [`ResourceSpatialManager`](../api/services/resource_spatial_manager.mdx) | Your layers are scoped to a `Resource`. |
| [`ModelDBSpatialManager`](../api/services/model_db_spatial_manager.mdx) | Your layers are scoped to a [`ModelDatabase`](../concepts/services.md). |
| [`ModelFileDBSpatialManager`](../api/services/model_file_db_spatial_manager.mdx) | Your layers are scoped to a `ModelDatabase` plus a `FileDatabase`. |

## Minimal subclass

```python
# my_first_app/services/spatial.py
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager


class MyFirstSpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'
    URI = 'http://app.aquaveo.com/my_first_app'
    GEOSERVER_CLUSTER_PORTS = (8081, 8082, 8083, 8084)

    SLD_PATH = '/path/to/your/sld/templates'
    SQL_PATH = '/path/to/your/sql'
```

The class attributes drive every GeoServer call the base class makes. Override them at the class level, or inject them via the constructor in your subclass.

## Use `reload_config` for mutating methods

When you write a method that mutates GeoServer (publishing a layer, updating a style), wrap it with the [`reload_config`](../api/services/base_spatial_manager.mdx) decorator from the same module. After the method runs, the decorator calls `self.reload(ports=self.GEOSERVER_CLUSTER_PORTS, public_endpoint=...)` so all nodes pick up the change.

```python
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager, reload_config


class MyFirstSpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'

    @reload_config()
    def publish_dam_layer(self, resource, **kwargs):
        # Publish layer through self.gs_engine ...
        return layer
```

The decorator inspects `kwargs['reload_config']` if present, otherwise falls back to `reload_config_default=True`. Pass `reload_config=False` from the caller to skip the reload (useful when you'll publish many layers in a loop and reload once at the end).

## Initialize the workspace and styles

The `atcore` console command sets up a default workspace + styles for the global `'atcore'` workspace:

```bash
atcore init --gsurl http://admin:geoserver@localhost:8181/geoserver/rest/
```

For your app's own workspace, call `engine.create_workspace(self.WORKSPACE, self.URI)` from a one-time admin script or extend `init_atcore` ([`tethysext.atcore.cli.init_command`](../api/cli/init_command.mdx)) for a custom CLI.

## Wire it into a `MapView`

```python
from tethysext.atcore.controllers.map_view import MapView
from .services.spatial import MyFirstSpatialManager, MyFirstMapManager


class ProjectMap(MapView):
    _MapManager = MyFirstMapManager
    _SpatialManager = MyFirstSpatialManager
```

See [Customize a Map View](./customize-a-map-view.md) for the full controller wiring.
