---
id: tutorials-walkthrough
title: End-to-End Walkthrough
sidebar_label: Walkthrough
sidebar_position: 1
---

# End-to-end walkthrough: a project + analysis app

This tutorial builds a small atcore-backed Tethys app from scratch. We'll create a `Project` resource, register the app-user pages, add a map page, and build a one-step analysis workflow that submits a Condor job. By the end, you'll have used every major atcore subsystem at least once.

If you're new to Tethys itself, finish [the Tethys tutorial](https://docs.tethysplatform.org/en/stable/tutorials.html) first — this walkthrough assumes you can already register URL maps, configure persistent stores, and build a Tethys gizmo template.

## Prerequisites

- atcore [installed](../getting-started/installation.md) into your Tethys environment.
- A PostgreSQL + PostGIS database reachable via a Tethys persistent store.
- A GeoServer instance reachable from Tethys.
- An HTCondor scheduler reachable from Tethys.

## 1. Scaffold the app

```bash
tethys scaffold my_first_app
cd tethysapp-my_first_app
tethys install -d
```

## 2. Define `Project`

```python
# my_first_app/models/__init__.py
from .projects import Project  # noqa
from .workflows import AnalysisWorkflow  # noqa
```

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

## 3. Define `AnalysisWorkflow`

```python
# my_first_app/models/workflows.py
from tethysext.atcore.models.app_users import ResourceWorkflow


class AnalysisWorkflow(ResourceWorkflow):
    TYPE = 'analysis'
    DISPLAY_TYPE_SINGULAR = 'Analysis'
    DISPLAY_TYPE_PLURAL = 'Analyses'

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

## 4. Build a SpatialManager and MapManager

```python
# my_first_app/services/spatial.py
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase
from tethys_sdk.gizmos import MapView, MVView


class MyFirstSpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'
    URI = 'http://app.aquaveo.com/my_first_app'


class MyFirstMapManager(MapManagerBase):
    def compose_map(self, request, *args, **kwargs):
        view = MVView(
            projection='EPSG:4326',
            center=self.DEFAULT_CENTER,
            zoom=self.DEFAULT_ZOOM,
            maxZoom=self.MAX_ZOOM,
            minZoom=self.MIN_ZOOM,
        )
        map_view = MapView(view=view, layers=[])
        # MapManagerBase.compose_map returns (MapView, extent)
        return map_view, [-180.0, -90.0, 180.0, 90.0]
```

This is the bare minimum — see [Customize a Map View](../how-to/customize-a-map-view.md) and [Extend the Spatial Manager](../how-to/extend-the-spatial-manager.md) for layer publishing.

## 5. Build a `MapView` controller

```python
# my_first_app/controllers/project_map.py
from tethysext.atcore.controllers.map_view import MapView
from ..services.spatial import MyFirstMapManager, MyFirstSpatialManager


class ProjectMap(MapView):
    map_title = 'Project Map'
    map_subtitle = ''
    template_name = 'atcore/map_view/map_view.html'
    _MapManager = MyFirstMapManager
    _SpatialManager = MyFirstSpatialManager
```

## 6. Wire `app.py`

Combine [the configuration page](../getting-started/configuration.md) with the new controllers and workflow:

```python
# my_first_app/app.py
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting
from tethysext.atcore.models.app_users import initialize_app_users_db
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.urls import (
    app_users as app_users_urls,
    resources as resources_urls,
    resource_workflows as rw_urls,
    spatial_reference as sr_urls,
)
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter

from .models import Project, AnalysisWorkflow
from .controllers.project_map import ProjectMap


def init_app_users_db(engine, first_time):
    initialize_app_users_db(engine, first_time=first_time)


class MyFirstApp(TethysAppBase):
    name = 'My First App'
    package = 'my_first_app'
    namespace = 'my_first_app'
    root_url = 'my-first-app'

    def persistent_store_settings(self):
        return (
            PersistentStoreDatabaseSetting(
                name='app_users_db',
                description='atcore database',
                initializer='my_first_app.app.init_app_users_db',
                spatial=True,
                required=True,
            ),
        )

    def permissions(self):
        pm = AppPermissionsManager(self.namespace)
        return PermissionsGenerator(pm).generate()

    def register_url_maps(self):
        UrlMap = url_map_maker(self.root_url)
        url_maps = [
            UrlMap(
                name='project_map',
                url='projects/{resource_id}/map',
                controller=ProjectMap.as_controller(
                    _app=self,
                    _persistent_store_name='app_users_db',
                ),
            ),
        ]

        url_maps += list(app_users_urls.urls(
            UrlMap, self, 'app_users_db',
            base_template='my_first_app/base.html',
        ))
        url_maps += list(resources_urls.urls(
            UrlMap, self, 'app_users_db',
            resource_model=Project,
            base_template='my_first_app/base.html',
        ))
        url_maps += list(rw_urls.urls(
            UrlMap, self, 'app_users_db',
            workflow_pairs=[(AnalysisWorkflow, ResourceWorkflowRouter)],
            base_template='my_first_app/base.html',
        ))
        url_maps += list(sr_urls.urls(
            UrlMap, self, 'app_users_db',
        ))

        return tuple(url_maps)
```

## 7. Sync and explore

```bash
tethys syncstores my_first_app
tethys manage start
```

Visit your app and click through to the projects, organizations, and users pages.

## 8. Create a workflow

In the shell or in a one-off controller, build an `AnalysisWorkflow` for an existing project:

```python
# example
from tethysext.atcore.models.resource_workflow_steps import (
    SpatialInputRWS, SpatialCondorJobRWS, ResultsResourceWorkflowStep,
)
from my_first_app.models import AnalysisWorkflow

workflow = AnalysisWorkflow(name='Demo analysis', resource=project, creator=app_user)
workflow.steps.extend([
    SpatialInputRWS(name='Pick area', order=1),
    SpatialCondorJobRWS(name='Run', order=2),
    ResultsResourceWorkflowStep(name='Results', order=3),
])
session.add(workflow)
session.commit()
```

Then redirect to:

```
{% url 'my_first_app:analysis_workflow' resource_id=project.id workflow_id=workflow.id %}
```

The workflow router takes over — see [Build a Resource Workflow](../how-to/build-a-resource-workflow.md) and [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md) for the next layer of customization.

## What you built

- A custom `Resource` (`Project`) with full CRUD via [`urls.resources`](../api/urls/resources.mdx).
- A custom `MapView` backed by your own `MapManager` and `SpatialManager`.
- A custom `ResourceWorkflow` (`AnalysisWorkflow`) with three steps, dispatched by [`ResourceWorkflowRouter`](../api/controllers/resource_workflows/resource_workflow_router.mdx#resourceworkflowrouter).
- App-users / organizations / spatial-reference pages courtesy of atcore's `urls(...)` factories.

## Where to go next

- [Concepts](../concepts/overview.md) for the rationale behind each piece — especially [App Users](../concepts/app-users.md) and [File Database](../concepts/file-database.md), which this walkthrough only grazes.
- [API Reference](../api/index.mdx) for the full class signatures.
