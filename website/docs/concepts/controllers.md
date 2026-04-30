---
id: concepts-controllers
title: Controllers
sidebar_label: Controllers
sidebar_position: 5
---

# Controllers

atcore ships class-based Tethys controllers (`TethysController` subclasses) that handle the recurring patterns: pages bound to an `AppUser` + `Resource`, map views, workflow views, and admin pages for app users / organizations / resources.

## The base hierarchy

The fundamental base view is [`ResourceView`](../api/controllers/resource_view.mdx#resourceview). It does three things on every request:

1. Wraps `get` and `post` with [`active_user_required`](../api/services/app_users/decorators.mdx) and [`resource_controller`](../api/services/app_users/decorators.mdx). The first redirects unauthenticated or disabled users; the second resolves `resource_id` from the URL into a `Resource` instance and opens a SQLAlchemy session.
2. Calls subclass hooks: `on_get` (pre-GET hook), `get_context` (extend the template context), and `request_to_method` (POST routes through this — it derives the handler from a `method` POST/GET parameter and dispatches to that named method on the class).
3. Renders `template_name` with a context that includes the `resource`, `back_url`, `base_template`, and any extras from `get_context`.

To build a resource-aware page, subclass `ResourceView`, set `template_name`, and override `get_context` (and optionally `on_post`).

## MapView

[`MapView`](../api/controllers/map_view.mdx#mapview) extends `ResourceView` and produces a Tethys map page driven by a `MapManager` and `SpatialManager` pair (see [Services](./services.md)). It expects two class attributes set by the subclass:

- `_MapManager` — your `MapManager` subclass.
- `_SpatialManager` — your `SpatialManager` subclass (typically derived from [`BaseSpatialManager`](../api/services/base_spatial_manager.mdx)).

`MapView` calls `map_manager.compose_map(...)` to build the map, applies layout tweaks (sets the map height/width, disables the default legend), and exposes hooks for adding custom layers, plots, and toolbar items.

## App-user CRUD pages

Under [`controllers.app_users`](../api/controllers/app_users/index.mdx):

- [`ManageUsers`](../api/controllers/app_users/manage_users.mdx), [`ModifyUser`](../api/controllers/app_users/modify_user.mdx), [`AddExistingUser`](../api/controllers/app_users/add_existing_user.mdx), [`UserAccount`](../api/controllers/app_users/user_account.mdx) — user management.
- [`ManageOrganizations`](../api/controllers/app_users/manage_organizations.mdx), [`ModifyOrganization`](../api/controllers/app_users/modify_organization.mdx), [`ManageOrganizationMembers`](../api/controllers/app_users/manage_organization_members.mdx) — org management.
- [`ManageResources`](../api/controllers/app_users/manage_resources.mdx), [`ModifyResource`](../api/controllers/app_users/modify_resource.mdx), [`ResourceDetails`](../api/controllers/app_users/resource_details.mdx), [`ResourceStatus`](../api/controllers/app_users/resource_status.mdx) — resource management.

Wire them via the `urls(...)` helpers — see [App Users](./app-users.md) and [Resources](./resources.md).

The mixins these views compose with — `AppUsersViewMixin`, `ResourceBackUrlViewMixin`, `ResourceViewMixin`, `MultipleResourcesViewMixin` — are documented in [`controllers.app_users.mixins`](../api/controllers/app_users/mixins.mdx).

## REST controllers

Under [`controllers.rest`](../api/controllers/rest/index.mdx):

- [`QuerySpatialReference`](../api/controllers/rest/spatial_reference.mdx) — backs the [`SpatialReferenceSelect`](./gizmos.md) gizmo with EPSG lookups against `spatial_ref_sys`.

## Workflow controllers

See [Resource Workflows](./resource-workflows.md). The router is [`ResourceWorkflowRouter`](../api/controllers/resource_workflows/resource_workflow_router.mdx#resourceworkflowrouter); the base view is [`ResourceWorkflowView`](../api/controllers/resource_workflows/workflow_view.mdx).

## Tabbed resource details

[`TabbedResourceDetails`](../api/controllers/resources/tabbed_resource_details.mdx) renders a tabbed page composed of tab classes ([`controllers.resources.tabs`](../api/controllers/resources/tabs/index.mdx)). Use it instead of `ResourceDetails` when one detail page isn't enough.

Built-in tab classes:

- [`ResourceSummaryTab`](../api/controllers/resources/tabs/summary_tab.mdx) — name / status / created-by header card; subclass and override `get_summary_tab_info` to add columns.
- [`ResourceFilesTab`](../api/controllers/resources/tabs/files_tab.mdx) — listing of `FileCollection`s attached to the resource.
- [`ResourceWorkflowsTab`](../api/controllers/resources/tabs/workflows_tab.mdx) — list of `ResourceWorkflow`s plus a "new workflow" launcher; subclass and override `get_workflow_types` to filter the launcher menu by resource state.
- [`ResourceListTab`](../api/controllers/resources/tabs/resource_list_tab.mdx) — list of child resources for a parent resource.

Compose them on a subclass:

```python
# tethysapp/myapp/controllers/resources/project_details.py
from tethysext.atcore.controllers.resources import (
    TabbedResourceDetails, ResourceSummaryTab,
    ResourceFilesTab, ResourceWorkflowsTab,
)


class ProjectSummaryTab(ResourceSummaryTab):
    def get_summary_tab_info(self, request, session, resource):
        return {
            'general': {
                'title': 'General',
                'columns': [
                    [('Region', resource.get_attribute('region') or '-')],
                    [('Inputs', resource.get_attribute('input_count') or 0)],
                ],
            },
        }


class ProjectDetails(TabbedResourceDetails):
    template_name = 'myapp/project_details.html'
    tabs = (
        {'slug': 'summary', 'title': 'Summary', 'view': ProjectSummaryTab},
        {'slug': 'files', 'title': 'Files', 'view': ResourceFilesTab},
        {'slug': 'workflows', 'title': 'Workflows', 'view': ResourceWorkflowsTab},
    )
```

`TabbedResourceDetails` requires a `{tab_slug}` URL kwarg, which the default `urls.resources.urls(...)` helpers don't emit. Register the URL by hand:

```python
# tethysapp/myapp/app.py — register_url_maps
url_maps += [
    UrlMap(
        name='project_details_tab',
        url='projects/{resource_id}/{tab_slug}',
        controller=ProjectDetails.as_controller(
            _app=self,
            _persistent_store_name='primary_db',
            _AppUser=MyAppUser,
            _Organization=MyOrganization,
            _Resource=Project,
            _PermissionsManager=MyPermissionsManager,
        ),
    ),
]
```

The leading-underscore kwargs to `as_controller(...)` are the convention for populating the view mixin slots — `AppUsersViewMixin._AppUser`, `ResourceViewMixin._Resource`, etc. The atcore URL helpers fill them automatically; when you register a URL by hand, you fill them yourself.

See [Add a tabbed resource details page](../how-to/add-a-tabbed-resource-details-page.md) for the full recipe.

## Decorators

You'll typically inherit auth/session handling from `ResourceView`. If you write a free-function controller and still want atcore's behavior, the building blocks are exported by [`services.app_users.decorators`](../api/services/app_users/decorators.mdx):

- `active_user_required()`
- `resource_controller(is_rest_controller=False)`

For permission checks themselves, use Tethys's own `permission_required` / `has_permission` from `tethys_sdk.permissions`.
