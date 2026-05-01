---
id: concepts-overview
title: Overview
sidebar_label: Overview
sidebar_position: 1
---

# What atcore is (and isn't)

`tethysext-atcore` is a Tethys Platform extension that provides reusable parts for the kind of data-heavy, organization-aware web apps Aquaveo tends to build. Drop it in alongside Tethys, then subclass and configure rather than rebuilding the same models, controllers, and permissions in every app.

## What atcore gives you

The package layout under [`tethysext/atcore/`](https://github.com/Aquaveo/tethysext-atcore/tree/master/tethysext/atcore) maps directly to the [API reference](../api/index.mdx):

| Subpackage | Purpose |
| --- | --- |
| [`models`](../api/models/index.mdx) | SQLAlchemy models — `AppUser`, `Organization`, `Resource`, `ResourceWorkflow`, workflow steps and results, `FileDatabase`. |
| [`controllers`](../api/controllers/index.mdx) | Class-based Tethys controllers — `MapView`, `ResourceView`, app-user CRUD pages, workflow router, REST endpoints. |
| [`services`](../api/services/index.mdx) | Stateful helpers — permissions manager, spatial managers, model database manager, condor workflow managers, file database client. |
| [`urls`](../api/urls/index.mdx) | `urls(...)` factory functions that emit `UrlMap` tuples for the app-user, resource, workflow, and spatial-reference URL groups. |
| [`gizmos`](../api/gizmos/index.mdx) | Tethys gizmos: [`SlideSheet`](../api/gizmos/slide_sheet.mdx) and [`SpatialReferenceSelect`](../api/gizmos/spatial_reference_select.mdx). |
| [`mixins`](../api/mixins/index.mdx) | Behavior mixins that the models compose — status, attributes, options, results, user lock, serialize, file collection. |
| [`permissions`](../api/permissions/index.mdx) | The `PermissionsGenerator` that builds the role/license permission matrix. |
| [`forms`](../api/forms/index.mdx) | Custom form widgets. |
| [`exceptions`](../api/exceptions/index.mdx) | The `ATCoreException` family. |
| [`cli`](../api/cli/index.mdx) | The `atcore` console command (currently `atcore init`). |

## How the pieces fit

A typical atcore-backed page looks like this:

1. A `urls(...)` helper from [`tethysext.atcore.urls`](../api/urls/index.mdx) registers a `UrlMap` that points at one of atcore's class-based controllers.
2. The controller (e.g. [`MapView`](../api/controllers/map_view.mdx) or [`ResourceWorkflowRouter`](../api/controllers/resource_workflows/resource_workflow_router.mdx)) is a `TethysController` subclass that uses a SQLAlchemy session against the app's app-users persistent store.
3. Decorators in [`services.app_users.decorators`](../api/services/app_users/decorators.mdx) wrap controller methods with auth checks (`active_user_required`, `resource_controller`).
4. The controller looks up an [`AppUser`](../api/models/app_users/app_user.mdx#appuser) and a [`Resource`](../api/models/app_users/resource.mdx#resource) for the request, and an [`AppPermissionsManager`](../api/services/app_users/permissions_manager.mdx#apppermissionsmanager) decides what the user can do.
5. For long-running work, a [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx) or [`ResourceWorkflowCondorJobManager`](../api/services/workflow_manager/condor_workflow_manager.mdx) submits Condor jobs that update the resource's status when they finish.

## What atcore is not

- **Not a Tethys replacement.** You still build a normal Tethys app — atcore plugs into it.
- **Not a generic ORM.** The SQLAlchemy models are tailored to the app-user / organization / resource / workflow domain. Use them as-is or subclass; don't expect them to model arbitrary domains.
- **Not opinion-free.** atcore assumes Postgres + PostGIS, an app-users persistent store, GeoServer for spatial layers, and HTCondor for batch jobs. You can stub or replace pieces, but the defaults are concrete.

## Where to go next

- New to the project? Start with [Installation](../getting-started/installation.md).
- Planning an atcore-backed app's layout? Read [Project Structure](./project-structure.md) for the two-package adapter pattern.
- Building your first atcore page? Read [App Users](./app-users.md) and [Resources](./resources.md), then [Controllers](./controllers.md).
- Need the full class signatures? Jump to the [API Reference](../api/index.mdx).
