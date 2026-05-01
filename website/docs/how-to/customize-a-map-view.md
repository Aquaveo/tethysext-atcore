---
id: how-to-customize-a-map-view
title: Customize a Map View
sidebar_label: Customize a map view
sidebar_position: 3
---

# Customize a map view

Build a `MapView` page for a custom resource. You'll need a [`Resource`](../concepts/resources.md) subclass and a [`SpatialManager`](../concepts/services.md) subclass.

## 1. Define a SpatialManager and MapManager

Add layers in `compose_map(...)`. It returns a `(MapView, extent)` tuple: a Tethys `MapView` gizmo configuration and a 4-list extent.

```python
# myapp/services/spatial.py
from tethys_sdk.gizmos import MapView, MVLayer, MVView
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class MyAppSpatialManager(BaseSpatialManager):
    WORKSPACE = 'myapp'
    URI = 'http://app.aquaveo.com/myapp'


class MyAppMapManager(MapManagerBase):
    DEFAULT_CENTER = [-98.5, 39.5]
    DEFAULT_ZOOM = 4

    def compose_map(self, request, resource_id=None, *args, **kwargs):
        view = MVView(
            projection='EPSG:4326',
            center=self.DEFAULT_CENTER,
            zoom=self.DEFAULT_ZOOM,
            maxZoom=self.MAX_ZOOM,
            minZoom=self.MIN_ZOOM,
        )

        layers = []

        # 1) A static GeoJSON layer for the resource's area-of-interest.
        if self.resource and self.resource.area_of_interest is not None:
            layers.append(self._compose_aoi_layer(self.resource))

        # 2) A WMS layer published by GeoServer for the project's basemap.
        wms_url = self.spatial_manager.get_ows_endpoint() + '/wms'
        layers.append(MVLayer(
            source='ImageWMS',
            options={
                'url': wms_url,
                'params': {'LAYERS': f'{self.spatial_manager.WORKSPACE}:streams'},
                'serverType': 'geoserver',
                'crossOrigin': 'anonymous',
            },
            legend_title='Streams',
            layer_options={'visible': True},
        ))

        # 3) Group layers for the layer-toggle UI.
        layer_groups = [
            self.build_layer_group(
                id='resource_layers',
                display_name=f'{self.resource.name} layers',
                layers=layers,
                layer_control='checkbox',
            ),
        ]

        map_view = MapView(
            view=view,
            layers=layers,
            basemap='OpenStreetMap',
            controls=['ZoomSlider', 'FullScreen', 'ScaleLine'],
        )

        # MapManagerBase.compose_map returns (MapView, extent)
        extent = self.get_map_extent()
        return map_view, extent

    def _compose_aoi_layer(self, resource):
        geojson = {
            'type': 'FeatureCollection',
            'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
            'features': [{
                'type': 'Feature',
                'geometry': resource.get_extent_as_geojson() if hasattr(
                    resource, 'get_extent_as_geojson'
                ) else None,
                'properties': {'name': resource.name},
            }],
        }
        return MVLayer(
            source='GeoJSON',
            options=geojson,
            legend_title=f'{resource.name} — AOI',
            layer_options={'style': {'fill': {'color': 'rgba(52,152,219,0.4)'}}},
        )
```

The base class also exposes [`COLOR_RAMPS`](../api/services/color_ramps.mdx) for thematic styling, plus `build_layer_group(...)` and `build_legend_item(...)` helpers for the layer-toggle UI.

:::tip Where layer URLs come from
For PostGIS-backed layers published through `ModelDBSpatialManager`, the WMS / WFS URL points at GeoServer with the resource's `ModelDatabase` as the datastore. For static GeoJSON, build the geometry in-process and hand it to `MVLayer(source='GeoJSON', options={...})`. Mixing both on one map is fine.
:::

## 2. Subclass `MapView`

```python
# myapp/controllers/project_map.py
from tethysext.atcore.controllers.map_view import MapView
from ..services.spatial import MyAppMapManager, MyAppSpatialManager


class ProjectMap(MapView):
    map_title = 'Project Map'
    map_subtitle = 'Inputs and outputs'
    template_name = 'myapp/project_map.html'

    _MapManager = MyAppMapManager
    _SpatialManager = MyAppSpatialManager

    geocode_enabled = True
    properties_popup_enabled = True
    show_legends = True
```

`MapView` wires the auth check, resource lookup, and slide sheet; override only what you need.

Common hooks:

- `get_context(request, session, resource, context, *args, **kwargs)` — extend the template context.
- `get_map_manager(request, resource, *args, **kwargs)` — return a custom manager instance per request.
- `should_disable_basemap(request, resource, map_manager)` — toggle the basemap.
- `on_get` — short-circuit a GET before the default rendering. POST handlers go through `request_to_method` (the `method` POST parameter selects the handler by name).

## 3. Reuse `MapView`'s template

The default template is `atcore/map_view/map_view.html`. To extend it, set `template_name` on your subclass and `{% extends 'atcore/map_view/map_view.html' %}` in your template, overriding the blocks you want.

For tweaks like the page subtitle or layer-tab name, just set the class attributes (`map_subtitle`, `layer_tab_name`) and keep the default template.

## 4. Register the URL

```python
# myapp/app.py
from .controllers.project_map import ProjectMap

UrlMap(
    name='project_map',
    url='projects/{resource_id}/map',
    controller=ProjectMap.as_controller(
        _app=self,
        _persistent_store_name='primary_db',
    ),
)
```

`MapView` extends [`ResourceView`](../api/controllers/resource_view.mdx#resourceview), so `_app` and `_persistent_store_name` are required `as_controller` kwargs. If you subclassed `Resource`, also pass `_Resource=Project` so the controller resolves your subclass on lookup.

## See also

- [`MapView`](../api/controllers/map_view.mdx#mapview) class docs.
- [Services](../concepts/services.md) — choosing between `ResourceSpatialManager` and `ModelDBSpatialManager`.
- [`SlideSheet`](../concepts/gizmos.md) — already integrated into `MapView` for layer / feature details.
