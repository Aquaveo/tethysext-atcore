---
id: how-to-customize-a-map-view
title: Customize a Map View
sidebar_label: Customize a map view
sidebar_position: 3
---

# Customize a map view

This recipe builds a `MapView` page for a custom resource. You'll need a [`Resource`](../concepts/resources.md) subclass and a [`SpatialManager`](../concepts/services.md) subclass.

## 1. Define a SpatialManager and MapManager

```python
# my_first_app/services/spatial.py
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class MyFirstSpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'
    URI = 'http://app.aquaveo.com/my_first_app'


class MyFirstMapManager(MapManagerBase):
    def compose_map(self, request, *args, **kwargs):
        # Build your MVView and MVLayer list here.
        # Return: (MapView, extent) where extent is a 4-list of floats.
        ...
```

`compose_map(...)` is where you add layers. Use `tethys_gizmos.gizmo_options.MVView` and `MVLayer` (already imported by the base). The base class also exposes [`COLOR_RAMPS`](../api/services/color_ramps.mdx) for thematic styling.

## 2. Subclass `MapView`

```python
# my_first_app/controllers/project_map.py
from tethysext.atcore.controllers.map_view import MapView
from .services.spatial import MyFirstMapManager, MyFirstSpatialManager


class ProjectMap(MapView):
    map_title = 'Project Map'
    map_subtitle = 'Inputs and outputs'
    template_name = 'my_first_app/project_map.html'

    _MapManager = MyFirstMapManager
    _SpatialManager = MyFirstSpatialManager

    geocode_enabled = True
    properties_popup_enabled = True
    show_legends = True
```

`MapView` already wires the auth check, the resource lookup, and the slide sheet; you only override what you want to change.

Common hooks you can override (subclass and define):

- `get_context(request, session, resource, context, *args, **kwargs)` — extend the template context.
- `get_map_manager(request, resource, *args, **kwargs)` — return a custom manager instance per-request.
- `should_disable_basemap(request, resource, map_manager)` — toggle the basemap.
- `on_get` — short-circuit a GET before the default rendering. POST handlers go through `request_to_method` (the `method` POST parameter selects the handler by name).

## 3. Use `ResourceView`'s template

The default `MapView` template is `atcore/map_view/map_view.html`. To extend it, set `template_name` on your subclass and `{% extends 'atcore/map_view/map_view.html' %}` in your template, overriding the blocks you want.

If you only need to change the page subtitle or the layer-tab name, set those as class attributes (`map_subtitle`, `layer_tab_name`) and keep the default template.

## 4. Register the URL

```python
# my_first_app/app.py
from .controllers.project_map import ProjectMap

UrlMap(
    name='project_map',
    url='projects/{resource_id}/map',
    controller=ProjectMap.as_controller(
        _app=self,
        _persistent_store_name='app_users_db',
    ),
)
```

`MapView` extends [`ResourceView`](../api/controllers/resource_view.mdx#resourceview), so `_app` and `_persistent_store_name` are required `as_controller` kwargs.

## See also

- [`MapView`](../api/controllers/map_view.mdx#mapview) class docs.
- [Services](../concepts/services.md) — when to choose `ResourceSpatialManager` vs. `ModelDBSpatialManager`.
- [`SlideSheet`](../concepts/gizmos.md) — already integrated into `MapView` for layer / feature details.
