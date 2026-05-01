---
id: tutorials-walkthrough
title: End-to-End Walkthrough
sidebar_label: Walkthrough
sidebar_position: 1
---

# End-to-end walkthrough: a project + analysis app

A small atcore-backed Tethys app, from scratch. A `Project` resource, the app-user pages, a map page that actually shows a layer, and a one-step analysis workflow that submits a Condor job. Touches every major atcore subsystem.

If you're new to Tethys, finish [the Tethys tutorial](https://docs.tethysplatform.org/en/stable/tutorials.html) first. This walkthrough assumes you can already register URL maps, configure persistent stores, and build a Tethys gizmo template.

:::tip Single-package vs. two-package layout
Larger atcore apps split the domain layer into a sibling adapter package — see [Project Structure](../concepts/project-structure.md). To keep things short, this walkthrough uses a single package. Refactor into two once your model and workflow code is more than a screenful.
:::

## Prerequisites

- atcore [installed](../getting-started/installation.md) into your Tethys environment.
- A PostgreSQL + PostGIS database reachable via a Tethys persistent store.
- A GeoServer instance reachable from Tethys.
- An HTCondor scheduler reachable from Tethys (only needed for the workflow step at the end).

## 1. Scaffold the app

```bash
tethys scaffold my_first_app
cd tethysapp-my_first_app
tethys install -d
```

Add atcore to your `install.yml` requirements if it isn't already pulled in transitively.

## 2. Define `Project`

Three pieces: a polymorphic identity, a geometry column for the area-of-interest, and a status key for "is this ready to use." Most other state stays on the inherited JSON `_attributes` blob.

```python
# my_first_app/models/__init__.py
from .projects import Project  # noqa
from .workflows import AnalysisWorkflow  # noqa
```

```python
# my_first_app/models/projects.py
from geoalchemy2 import Geometry
from sqlalchemy import Column
from tethysext.atcore.models.app_users import Resource


class Project(Resource):
    TYPE = 'project'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'

    STATUS_KEY_INIT = 'init'

    area_of_interest = Column(Geometry('POLYGON', 4326))

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

## 3. Define `AnalysisWorkflow`

Workflows expose a `new()` factory that takes the runtime context and builds the step graph. See [the `new()` factory](../concepts/resource-workflows.md#the-new-factory) for why.

```python
# my_first_app/models/workflows.py
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps import (
    SpatialInputRWS,
    SpatialCondorJobRWS,
    ResultsResourceWorkflowStep,
)
from tethysext.atcore.services.app_users.roles import Roles


def build_jobs_callback(workflow, step, *args, **kwargs):
    """Returns the CondorWorkflowJobNode dict list for this run.

    Called by SpatialCondorJobRWS at submit time so it can read fresh
    workflow state. Returning an empty list is fine for a tutorial — the
    job runner will succeed immediately.
    """
    return []


class AnalysisWorkflow(ResourceWorkflow):
    TYPE = 'analysis'
    DISPLAY_TYPE_SINGULAR = 'Analysis'
    DISPLAY_TYPE_PLURAL = 'Analyses'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    @classmethod
    def new(cls, app, name, resource_id, creator_id,
            geoserver_name, map_manager, spatial_manager, **kwargs):
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id)

        pick_step = SpatialInputRWS(
            name='Pick study area',
            order=1,
            help='Draw or upload your area of interest.',
            options={
                'shapes': ['polygons', 'extents'],
                'singular_name': 'Area of Interest',
                'plural_name': 'Areas of Interest',
                'allow_shapefile': True,
                'allow_drawing': True,
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )

        run_step = SpatialCondorJobRWS(
            name='Run analysis',
            order=2,
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_jobs_callback,
                'workflow_kwargs': {},
                'working_message': 'Running analysis...',
                'error_message': 'Analysis failed.',
                'pending_message': 'Analysis pending.',
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )
        run_step.parents.append(pick_step)

        results_step = ResultsResourceWorkflowStep(
            name='Results',
            order=3,
        )
        run_step.result = results_step

        workflow.steps.extend([pick_step, run_step, results_step])
        return workflow
```

## 4. Build a SpatialManager and MapManager

The MapManager renders a static GeoJSON layer for the project's `area_of_interest` so step 7 has something to verify against — a polygon should appear when you open the map page.

```python
# my_first_app/services/spatial.py
from tethys_sdk.gizmos import MapView, MVLayer, MVView
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.services.map_manager import MapManagerBase


class MyFirstSpatialManager(BaseSpatialManager):
    WORKSPACE = 'my_first_app'
    URI = 'http://app.aquaveo.com/my_first_app'


class MyFirstMapManager(MapManagerBase):
    DEFAULT_CENTER = [-98.5, 39.5]   # rough US centroid
    DEFAULT_ZOOM = 4
    MAX_ZOOM = 18
    MIN_ZOOM = 2

    def compose_map(self, request, *args, **kwargs):
        view = MVView(
            projection='EPSG:4326',
            center=self.DEFAULT_CENTER,
            zoom=self.DEFAULT_ZOOM,
            maxZoom=self.MAX_ZOOM,
            minZoom=self.MIN_ZOOM,
        )

        layers = []
        if self.resource and self.resource.area_of_interest is not None:
            geojson = {
                'type': 'FeatureCollection',
                'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
                'features': [{
                    'type': 'Feature',
                    'geometry': self.resource.get_extent_as_geojson() if hasattr(
                        self.resource, 'get_extent_as_geojson'
                    ) else None,
                    'properties': {'name': self.resource.name},
                }],
            }
            aoi_layer = MVLayer(
                source='GeoJSON',
                options=geojson,
                legend_title=f'{self.resource.name} — area of interest',
                layer_options={'style': {'fill': {'color': 'rgba(52,152,219,0.4)'}}},
                feature_selection=False,
            )
            layers.append(aoi_layer)

        map_view = MapView(
            view=view,
            layers=layers,
            basemap='OpenStreetMap',
            controls=['ZoomSlider', 'FullScreen', 'ScaleLine'],
        )
        # MapManagerBase.compose_map returns (MapView, extent)
        extent = [-180.0, -90.0, 180.0, 90.0]
        return map_view, extent
```

A fresh project with no `area_of_interest` renders an empty map over the basemap. That's the expected first-load state.

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

## 6. Build a "start workflow" controller

Normally this would be a button on the project details page or the workflows tab. Here it's just a URL you hit manually.

```python
# my_first_app/controllers/start_analysis.py
from django.http import HttpResponseRedirect
from django.urls import reverse
from tethys_sdk.routing import controller

from ..app import MyFirstApp as app
from ..models import Project, AnalysisWorkflow
from ..services.spatial import MyFirstMapManager, MyFirstSpatialManager


@controller(
    name='start_analysis',
    url='my-first-app/projects/{resource_id}/analysis/start',
    app_workspace=False,
)
def start_analysis(request, resource_id):
    Session = app.get_persistent_store_database('app_users_db', as_sessionmaker=True)
    session = Session()
    try:
        project = session.query(Project).get(resource_id)
        creator = request.user.username  # AppUser.username mirrors Django username
        spatial_manager = MyFirstSpatialManager(geoserver_engine=None)
        map_manager = MyFirstMapManager(spatial_manager=spatial_manager, resource=project)

        workflow = AnalysisWorkflow.new(
            app=app,
            name=f'Analysis for {project.name}',
            resource_id=project.id,
            creator_id=creator,
            geoserver_name='primary_geoserver',
            map_manager=map_manager,
            spatial_manager=spatial_manager,
        )
        session.add(workflow)
        session.commit()

        return HttpResponseRedirect(reverse(
            'my_first_app:analysis_workflow',
            kwargs={'resource_id': project.id, 'workflow_id': workflow.id},
        ))
    finally:
        session.close()
```

The redirect target name comes from the URL helper. The pattern is `<workflow_type>_workflow` and `AnalysisWorkflow.TYPE` is `'analysis'`.

## 7. Wire `app.py`

Four atcore URL helpers, one app. `app_users.urls(custom_resources={...})` registers the user, organization, and `Project` CRUD pages in a single call.

```python
# my_first_app/app.py
from tethys_sdk.app_settings import (
    PersistentStoreDatabaseSetting,
    SchedulerSetting,
    SpatialDatasetServiceSetting,
)
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter
from tethysext.atcore.models.app_users import initialize_app_users_db
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager
from tethysext.atcore.urls import (
    app_users as app_users_urls,
    resource_workflows as rw_urls,
    spatial_reference as sr_urls,
)

from .controllers.project_map import ProjectMap
from .models import AnalysisWorkflow, Project


def init_app_users_db(engine, first_time):
    # Importing the models inside the initializer ensures the SQLAlchemy
    # mappers are registered before create_all runs.
    from .models import projects, workflows  # noqa
    initialize_app_users_db(engine, first_time=first_time)


class MyFirstApp(TethysAppBase):
    name = 'My First App'
    package = 'my_first_app'
    namespace = 'my_first_app'
    root_url = 'my-first-app'

    SCHEDULER_NAME = 'remote_cluster'

    def persistent_store_settings(self):
        return (
            PersistentStoreDatabaseSetting(
                name='app_users_db',
                description='atcore app-users database',
                initializer='my_first_app.app.init_app_users_db',
                spatial=True,
                required=True,
            ),
        )

    def spatial_dataset_service_settings(self):
        return (
            SpatialDatasetServiceSetting(
                name='primary_geoserver',
                description='Primary GeoServer',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=False,
            ),
        )

    def scheduler_settings(self):
        return (
            SchedulerSetting(
                name=self.SCHEDULER_NAME,
                description='HTCondor scheduler',
                engine=SchedulerSetting.CONDOR,
                required=False,
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

        # User / organization / Project CRUD in one call.
        url_maps += list(app_users_urls.urls(
            url_map_maker=UrlMap, app=self,
            persistent_store_name='app_users_db',
            custom_resources={Project: []},
            base_template='my_first_app/base.html',
        ))

        url_maps += list(rw_urls.urls(
            url_map_maker=UrlMap, app=self,
            persistent_store_name='app_users_db',
            workflow_pairs=((AnalysisWorkflow, ResourceWorkflowRouter),),
            base_template='my_first_app/base.html',
        ))

        url_maps += list(sr_urls.urls(
            url_map_maker=UrlMap, app=self,
            persistent_store_name='app_users_db',
        ))

        return tuple(url_maps)
```

## 8. Sync and explore

```bash
tethys syncstores my_first_app
tethys manage start
```

Then:

1. Visit `/apps/my-first-app/users/` → atcore's `ManageUsers` page.
2. Visit `/apps/my-first-app/organizations/` → `ManageOrganizations`. Create an organization.
3. Visit `/apps/my-first-app/projects/` → `ManageResources` for `Project`. Click **New** and create a project. The form takes a name and description; the area-of-interest gets set later via a custom modify form.
4. Click into the project, then visit `/apps/my-first-app/projects/<resource_id>/map` to see the map page.
5. Hit `/apps/my-first-app/projects/<resource_id>/analysis/start` to launch an `AnalysisWorkflow`. atcore redirects into the `ResourceWorkflowRouter`, which dispatches to the `SpatialInputRWS` view.

### Expected map state

- Fresh project (no AOI): OpenStreetMap basemap centered on the US, no overlay layers, empty legend.
- Project with AOI: basemap plus a translucent blue polygon for the area-of-interest, with the project's name in the legend.

If the map page returns a 500, the usual culprit is a missing `MyFirstApp.permissions()` registration. atcore's `MapView` uses `active_user_required`, which expects the permission groups to exist.

## 9. Where the workflow goes from here

Once you redirect into the router:

- It picks the first incomplete step (the `SpatialInputRWS` named "Pick study area").
- It dispatches to `controllers.resource_workflows.map_workflows.SpatialInputMWV`, which renders a draw-tools map.
- After you draw a polygon and submit, the `SpatialCondorJobRWS` named "Run analysis" becomes active.
- Submitting that step calls `build_jobs_callback`, which returns an empty job list. atcore submits the no-op Condor workflow, marks the step `STATUS_COMPLETE`, and reveals the `ResultsResourceWorkflowStep`.

Swap `build_jobs_callback` for real `CondorWorkflowJobNode` dicts to make the step do actual work — see [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md).

## What you built

- A custom `Resource` (`Project`) with a PostGIS geometry column, registered through `app_users.urls(custom_resources=...)`.
- A custom `MapView` backed by your own `MapManager` and `SpatialManager`, rendering a GeoJSON layer.
- A custom `ResourceWorkflow` (`AnalysisWorkflow`) using the `new()` factory contract — three steps, role-gated, with `parents` and `result` wired up.
- A "start workflow" controller that materializes a workflow and redirects into the router.
- App-users / organizations / spatial-reference pages from atcore's `urls(...)` factories.

## Where to go next

- [Project Structure](../concepts/project-structure.md) — refactoring into a two-package adapter layout once the app grows.
- [Add a tabbed resource details page](../how-to/add-a-tabbed-resource-details-page.md) — replace the default project details with `TabbedResourceDetails`.
- [Add a custom workflow step type](../how-to/add-a-custom-workflow-step-type.md) — when the built-in step types don't fit.
- [Wire up a file database](../how-to/wire-up-a-file-database.md) — give `Project` on-disk inputs.
- [Build a Resource Workflow](../how-to/build-a-resource-workflow.md) and [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md).
