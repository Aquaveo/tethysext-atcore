---
id: how-to-add-a-tabbed-resource-details-page
title: Add a Tabbed Resource Details Page
sidebar_label: Add a tabbed resource details page
sidebar_position: 7
---

# Add a tabbed resource details page

The default `ResourceDetails` controller shows a single page per resource. When that outgrows the form, switch to [`TabbedResourceDetails`](../api/controllers/resources/tabbed_resource_details.mdx). It composes tab classes from [`controllers.resources.tabs`](../api/controllers/resources/tabs/index.mdx) into a tabbed view and works with the existing `ManageResources` / `ModifyResource` URL maps.

## 1. Choose your tabs

atcore ships these tab classes:

- [`ResourceSummaryTab`](../api/controllers/resources/tabs/summary_tab.mdx) — header card; subclass to add summary columns.
- [`ResourceFilesTab`](../api/controllers/resources/tabs/files_tab.mdx) — `FileCollection` listing.
- [`ResourceWorkflowsTab`](../api/controllers/resources/tabs/workflows_tab.mdx) — `ResourceWorkflow` listing plus new-workflow launcher.
- [`ResourceListTab`](../api/controllers/resources/tabs/resource_list_tab.mdx) — child resources.

Mix built-ins with your own subclasses.

## 2. Subclass `ResourceSummaryTab` for the summary card

```python
# myapp/controllers/resources/tabs/project_summary_tab.py
from tethysext.atcore.controllers.resources import ResourceSummaryTab


class ProjectSummaryTab(ResourceSummaryTab):
    def get_summary_tab_info(self, request, session, resource):
        return {
            'general': {
                'title': 'General',
                'columns': [
                    [('Region', resource.get_attribute('region') or '-')],
                    [('Inputs', resource.get_attribute('input_count') or 0)],
                    [('Status', resource.get_status('init') or 'unknown')],
                ],
            },
        }
```

`get_summary_tab_info` returns a dict of cards. Each card has `title` and `columns` (a list of column-lists of `(label, value)` tuples).

## 3. Customize the workflows tab (optional)

When the available workflow types depend on resource state (parents offer different workflows than leaves, etc.), subclass `ResourceWorkflowsTab` and override `get_workflow_types`:

```python
# myapp/controllers/resources/tabs/project_workflows_tab.py
from tethysext.atcore.controllers.resources import ResourceWorkflowsTab
from myapp_adapter.workflows import LEAF_WORKFLOWS, PARENT_WORKFLOWS


class ProjectWorkflowsTab(ResourceWorkflowsTab):
    def get_workflow_types(self, request, resource):
        return PARENT_WORKFLOWS if resource.children else LEAF_WORKFLOWS
```

The base returns a global `{TYPE: WorkflowClass}` dict; the override gates the launcher menu by resource state.

## 4. Compose the details controller

```python
# myapp/controllers/resources/project_details.py
from tethysext.atcore.controllers.resources import (
    TabbedResourceDetails, ResourceFilesTab,
)
from .tabs.project_summary_tab import ProjectSummaryTab
from .tabs.project_workflows_tab import ProjectWorkflowsTab


class ProjectDetails(TabbedResourceDetails):
    template_name = 'myapp/project_details.html'
    tabs = (
        {'slug': 'summary', 'title': 'Summary', 'view': ProjectSummaryTab},
        {'slug': 'files', 'title': 'Files', 'view': ResourceFilesTab},
        {'slug': 'workflows', 'title': 'Workflows', 'view': ProjectWorkflowsTab},
    )

    def get_context(self, request, session, resource, context, *args, **kwargs):
        context = super().get_context(request, session, resource, context, *args, **kwargs)
        # Gate UI on atcore-provided permissions.
        from tethys_sdk.permissions import has_permission
        context['can_manage_resources'] = has_permission(request, 'edit_resource')
        return context
```

## 5. Provide the template

The default tabbed template lives at `atcore/resources/tabbed_resource_details.html`. Extend it and override `app_navigation_items` (or any other block) to add app-specific chrome:

```html
{# tethysapp/myapp/templates/myapp/project_details.html #}
{% extends 'atcore/resources/tabbed_resource_details.html' %}

{% block app_navigation_items %}
  <li class="nav-item">
    <a class="nav-link" href="{% url 'myapp:projects_manage_resources' %}">
      All projects
    </a>
  </li>
{% endblock %}
```

## 6. Register the URL by hand

`TabbedResourceDetails` needs a `{tab_slug}` URL kwarg. The `app_users.urls(custom_resources=...)` and `resources.urls(...)` helpers don't emit it, so add the URL map yourself in `register_url_maps`:

```python
# myapp/app.py
from .controllers.resources.project_details import ProjectDetails
from myapp_adapter.resources.project import Project
from myapp_adapter.app_users.permissions import MyPermissionsManager
from myapp_adapter.app_users.organization import MyOrganization

url_maps += [
    UrlMap(
        name='project_details_tab',
        url='projects/{resource_id}/{tab_slug}',
        controller=ProjectDetails.as_controller(
            _app=self,
            _persistent_store_name='primary_db',
            _Organization=MyOrganization,
            _Resource=Project,
            _PermissionsManager=MyPermissionsManager,
        ),
    ),
]
```

The leading-underscore kwargs to `as_controller(...)` fill the view-mixin slots that atcore's controllers depend on. The URL helpers do this automatically — when you register a URL by hand, you do it yourself.

## 7. Link to a specific tab

```python
from django.urls import reverse
url = reverse('myapp:project_details_tab', kwargs={
    'resource_id': resource.id,
    'tab_slug': 'workflows',
})
```

The default redirect after a `ResourceDetails` action goes to `<slug>_resource_details`. Override `default_back_url` on your workflow router (and similar) so the user lands on the tab they came from.

## See also

- [`TabbedResourceDetails`](../api/controllers/resources/tabbed_resource_details.mdx) and the per-tab classes under [`controllers.resources.tabs`](../api/controllers/resources/tabs/index.mdx).
- [Controllers concept](../concepts/controllers.md#tabbed-resource-details).
