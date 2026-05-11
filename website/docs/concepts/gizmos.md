---
id: concepts-gizmos
title: Gizmos
sidebar_label: Gizmos
sidebar_position: 7
---

# Gizmos

atcore exports two custom Tethys [gizmos](https://docs.tethysplatform.org/en/stable/tethys_sdk/gizmos.html) — small reusable UI widgets your templates can render with the standard `{% gizmo %}` tag.

## SlideSheet

[`SlideSheet`](../api/gizmos/slide_sheet.mdx#slidesheet) is a slide-out panel anchored to the right edge of the page. Use it to host secondary content — layer details, plots, forms — without leaving the current view.

```python
# example — controller
from tethysext.atcore.gizmos import SlideSheet

slide_sheet = SlideSheet(
    id='layer-details',
    content_template='my_first_app/partials/layer_details.html',
    title='Layer Details',
)
context = {'slide_sheet': slide_sheet}
```

```html
{% load tethys_gizmos %}
{% gizmo slide_sheet %}
```

The widget loads its content from the template you point at via `content_template`. Open and close it from JavaScript using the id-suffixed handlers in `atcore/gizmos/slide_sheet/slide_sheet.js`.

`MapView` already integrates a `SlideSheet` for layer / feature details — see [`MapView`](../api/controllers/map_view.mdx#mapview).

## SpatialReferenceSelect

[`SpatialReferenceSelect`](../api/gizmos/spatial_reference_select.mdx#spatialreferenceselect) is a `select2`-backed lookup input for picking an EPSG spatial reference system by SRID or name.

```python
# example — controller
from tethysext.atcore.gizmos import SpatialReferenceSelect

srs_select = SpatialReferenceSelect(
    display_name='Coordinate System',
    name='srs',
    placeholder='Search by EPSG code or name...',
    spatial_reference_service=reverse('my_first_app:atcore_query_spatial_reference'),
    initial=('NAD83 / UTM zone 12N', '26912'),
)
```

The `spatial_reference_service` URL must point at the `atcore_query_spatial_reference` endpoint registered by [`tethysext.atcore.urls.spatial_reference.urls`](../api/urls/spatial_reference.mdx). Wire it once in your `app.py`:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import spatial_reference as sr_urls

url_maps = sr_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='primary_db',
)
```

The endpoint queries `spatial_ref_sys` via [`SpatialReferenceService`](../api/services/spatial_reference.mdx).

:::note
Both gizmos register their own JS/CSS via `get_gizmo_js` / `get_gizmo_css` and (for `SpatialReferenceSelect`) require `select2` from `vendor_static_dependencies`. As long as the gizmo is rendered through `{% gizmo %}`, Tethys handles the asset wiring.
:::
