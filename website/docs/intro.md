---
id: intro
title: Introduction
sidebar_label: Introduction
sidebar_position: 0
slug: /
---

# tethysext-atcore

`tethysext-atcore` is a [Tethys Platform](https://docs.tethysplatform.org) extension that ships reusable building blocks for data-driven scientific web apps: an app-user / organization / resource model, a generic resource-workflow engine, map and resource views, gizmos, spatial managers, and a file database. Use it as the foundation for an Aquaveo-style Tethys app instead of re-deriving these pieces in every project.

## What's inside

- **App users, organizations, and resources** — SQLAlchemy models plus controllers and URL helpers for managing them. See [App Users](./concepts/app-users.md) and [Resources](./concepts/resources.md).
- **Resource workflows** — a step-based engine for guiding users through multi-step processes (form input, spatial input, condor jobs, results). See [Resource Workflows](./concepts/resource-workflows.md).
- **Map and resource views** — base [controllers](./concepts/controllers.md) (`MapView`, `ResourceView`) you subclass to render resource-aware pages.
- **Spatial and model database services** — managers for GeoServer layers and per-resource model databases. See [Services](./concepts/services.md).
- **Permissions** — a license/role permissions matrix and an `AppPermissionsManager`. See [Permissions](./concepts/permissions.md).
- **Gizmos** — `SlideSheet`, `SpatialReferenceSelect`. See [Gizmos](./concepts/gizmos.md).
- **File database** — a SQL-tracked filesystem store. See [File Database](./concepts/file-database.md).

## How to read these docs

This site follows a [Diátaxis](https://diataxis.fr)-flavored layout:

- **[Getting Started](./getting-started/installation.md)** — install the extension and stand up a minimal Tethys app that uses it.
- **[Concepts](./concepts/overview.md)** — what each subsystem is for and how they fit together.
- **[How-to Guides](./how-to/add-a-resource-type.md)** — task-oriented recipes (subclass a resource, build a workflow, run a condor job).
- **[Tutorials](./tutorials/walkthrough.md)** — an end-to-end walkthrough of building a small atcore-based app.
- **[Reference](./reference/permissions-cheatsheet.md)** — quick-lookup tables for permissions and exceptions.
- **[API Reference](./api/index.mdx)** — auto-generated module documentation. Edit Python docstrings, not those pages.

:::tip
If you've never built a Tethys app, read the [Tethys Platform tutorial](https://docs.tethysplatform.org/en/stable/tutorials.html) first. These docs assume you already understand `TethysAppBase`, `UrlMap`, persistent stores, and gizmos.
:::

## Source

The Python source lives at [`tethysext/atcore/`](https://github.com/Aquaveo/tethysext-atcore/tree/master/tethysext/atcore). When narrative docs and source disagree, the source wins — please open an issue or PR.
