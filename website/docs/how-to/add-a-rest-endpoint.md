---
id: how-to-add-a-rest-endpoint
title: Add a REST Endpoint
sidebar_label: Add a REST endpoint
sidebar_position: 4
---

# Add a REST endpoint

atcore exposes one REST controller out of the box — [`QuerySpatialReference`](../api/controllers/rest/spatial_reference.mdx). To add your own, follow the same shape: a class that inherits from `TethysController`, returns `JsonResponse`, and is wired through a `UrlMap`.

## 1. Use the `resource_controller` decorator for resource-aware REST

If your endpoint operates on a `Resource`, decorate the method with [`resource_controller(is_rest_controller=True)`](../api/services/app_users/decorators.mdx). The flag tells atcore to return `JsonResponse({'success': False, 'error': ...})` on errors instead of a redirect.

```python
# my_first_app/controllers/rest/projects.py
from django.http import JsonResponse
from tethys_sdk.base import TethysController
from tethysext.atcore.services.app_users.decorators import (
    active_user_required, resource_controller,
)
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin


class ProjectStatus(ResourceViewMixin, TethysController):

    @active_user_required()
    @resource_controller(is_rest_controller=True)
    def get(self, request, session, resource, back_url, *args, **kwargs):
        return JsonResponse({
            'success': True,
            'status': resource.get_status(),
            'name': resource.name,
        })
```

`ResourceViewMixin` provides `get_resource_model()` and `get_sessionmaker()`, both used by `resource_controller` to load the resource.

## 2. Register the URL map

```python
# my_first_app/app.py — register_url_maps
from .controllers.rest.projects import ProjectStatus

UrlMap(
    name='rest_project_status',
    url='rest/projects/{resource_id}/status',
    controller=ProjectStatus.as_controller(
        _app=self,
        _persistent_store_name='app_users_db',
        _Resource=Project,
    ),
)
```

`as_controller` needs the same kwargs the management controllers do — at minimum `_app`, `_persistent_store_name`, and `_Resource`.

## 3. Use the `SpatialReferenceService` REST endpoint

If you only need EPSG lookups for the [`SpatialReferenceSelect`](../concepts/gizmos.md) gizmo, register it via [`tethysext.atcore.urls.spatial_reference.urls`](../api/urls/spatial_reference.mdx) — the controller is `QuerySpatialReference`, and you'd point your gizmo's `spatial_reference_service` URL at the `atcore_query_spatial_reference` URL name.

```python
# my_first_app/app.py — register_url_maps
from tethysext.atcore.urls import spatial_reference as sr_urls

url_maps += list(sr_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='primary_db',
))
```

## See also

- [`active_user_required`](../api/services/app_users/decorators.mdx) — auth helper.
- [`resource_controller`](../api/services/app_users/decorators.mdx) — error handling and resource lookup.
