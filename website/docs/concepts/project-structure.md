---
id: concepts-project-structure
title: Project Structure
sidebar_label: Project structure
sidebar_position: 1.5
---

# Project structure

A small atcore-backed Tethys app can live entirely inside a single `tethysapp.<name>` package. Once the app grows past a few resources and a workflow or two, the usual move is to split it into two Python packages:

- `tethysapp.<name>` — the Tethys app: `app.py`, controllers, templates, app-only services (e.g. the `MapManager`), and any wiring code that depends on Django or Tethys.
- `<name>-adapter` (sibling package, importable as `<name>_adapter`) — the domain core: SQLAlchemy models, `ResourceWorkflow` subclasses, custom `AppUser` / `Organization` / `Roles` / `Licenses`, the `SpatialManager`, and pure-Python services that should be testable without spinning up Tethys.

Atcore doesn't enforce the split, but it's the convention.

## Why split?

1. Condor jobs and CLIs can import your models without dragging in Django. A Condor worker that calls back to update a workflow status shouldn't have to boot a Tethys app context. Models in the adapter package load from anything with a SQLAlchemy session.
2. Domain-layer tests stay fast. Workflow definitions, `Resource` subclasses, and permission generators have no Tethys dependency, so unit tests run in milliseconds and don't need a persistent store.
3. Reuse across apps. A second app that wants the same `Resource` types or workflow steps imports the adapter package directly.
4. The adapter package is what the app *is*; the Tethys package is how the app is rendered.

## What goes where

| Concern | `tethysapp.<name>` | `<name>-adapter` |
| --- | --- | --- |
| `app.py` (`TethysAppBase` subclass) | yes | — |
| URL maps, `register_url_maps()` | yes | — |
| Tethys controllers (`MapView`, `TabbedResourceDetails`, ...) | yes | — |
| HTML templates, static assets | yes | — |
| `MapManagerBase` subclass (renders to Tethys gizmos) | yes | — |
| `Resource` / `SpatialResource` subclasses | — | yes |
| `ResourceWorkflow` subclasses + step composition | — | yes |
| `AppUser` / `Organization` subclasses | — | yes |
| `Roles` / `Licenses` subclasses | — | yes |
| `BaseSpatialManager` subclass (talks to GeoServer + SQL) | — | yes |
| `AppPermissionsManager` / `PermissionsGenerator` subclasses | — | yes |
| Condor job scripts | — | yes |
| Alembic migrations | yes (next to `app.py`) | — |

The Tethys package imports the adapter package when wiring URL maps and instantiating views. The adapter package never imports Tethys or Django.

## Single-package layout (for small apps)

If your app has one resource type and no workflows, keep everything in `tethysapp.<name>/`:

```
tethysapp-myapp/
└── tethysapp/
    └── myapp/
        ├── app.py
        ├── controllers/
        ├── models/           # Resource, Workflow subclasses live here
        ├── services/         # MapManager, SpatialManager
        └── templates/
```

The walkthrough tutorial uses the single-package layout. Refactor into two packages when the trade-offs above start to bite.

## Two-package layout

```
tethysapp-myapp/
├── tethysapp-myapp/                  # the Tethys app package
│   └── tethysapp/
│       └── myapp/
│           ├── app.py
│           ├── controllers/
│           │   ├── resources/        # ManageMyResources, ModifyMyResource, ...
│           │   ├── workflows/        # MyWorkflowRouter
│           │   └── workflow_steps/   # custom step views (MapWorkflowView subclasses)
│           ├── services/
│           │   └── map_manager.py    # MyMapManager(MapManagerBase)
│           └── templates/myapp/
└── myapp-adapter/                    # the domain package
    └── myapp_adapter/
        ├── app_users/
        │   ├── app_user.py           # MyAppUser(AppUser)
        │   ├── organization.py       # MyOrganization(Organization)
        │   └── permissions.py        # Roles, Licenses, PermissionsGenerator
        ├── resources/
        │   ├── project.py            # Project(Resource)
        │   ├── scenario.py           # Scenario(Resource)
        │   └── mixins/               # cross-cutting Resource mixins
        ├── workflows/
        │   ├── base_workflow.py      # MyWorkflow(ResourceWorkflow) — abstract
        │   └── analysis/             # one package per workflow type
        │       └── __init__.py       # AnalysisWorkflow.new(...)
        ├── workflow_steps/           # custom RWS subclasses
        ├── services/
        │   └── spatial_manager.py    # MySpatialManager(ResourceSpatialManager)
        └── job_scripts/              # Condor worker entry points
```

Wire the two together by adding the adapter package to your `pyproject.toml` / `install.yml` and importing from it wherever you need a domain class:

```python
# tethysapp/myapp/app.py
from myapp_adapter.resources.project import Project
from myapp_adapter.workflows.analysis import AnalysisWorkflow
from myapp_adapter.app_users.permissions import MyPermissionsGenerator
from .controllers.resources.manage_projects import ManageProjects, ModifyProject
from .controllers.workflows.my_workflow_router import MyWorkflowRouter
```

## Next

- [App Users](./app-users.md) — what lives in the `app_users/` adapter subpackage.
- [Resources](./resources.md) — patterns for the `resources/` subpackage, including the mixin idiom.
- [Resource Workflows](./resource-workflows.md) — the `new()` factory used by every workflow in the `workflows/` subpackage.
