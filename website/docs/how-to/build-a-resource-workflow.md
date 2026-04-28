---
id: how-to-build-a-resource-workflow
title: Build a Resource Workflow
sidebar_label: Build a resource workflow
sidebar_position: 2
---

# Build a resource workflow

This recipe walks through composing a custom workflow from the built-in step types and registering its URLs.

## 1. Subclass `ResourceWorkflow`

```python
# my_first_app/models/workflows.py
from tethysext.atcore.models.app_users import ResourceWorkflow


class AnalysisWorkflow(ResourceWorkflow):
    TYPE = 'analysis'
    DISPLAY_TYPE_SINGULAR = 'Analysis'
    DISPLAY_TYPE_PLURAL = 'Analyses'

    __mapper_args__ = {'polymorphic_identity': TYPE}
```

The workflow's steps and results are defined per-instance, not per-class — you build the step list in code when you create a workflow row.

## 2. Create the workflow with steps

```python
# example — controllers/start_analysis.py
from tethysext.atcore.models.resource_workflow_steps import (
    SpatialInputRWS, FormInputRWS, SpatialCondorJobRWS, ResultsResourceWorkflowStep,
)
from .models.workflows import AnalysisWorkflow


def start_analysis(session, resource, app_user):
    workflow = AnalysisWorkflow(
        name=f'Analysis for {resource.name}',
        resource=resource,
        creator=app_user,
    )

    workflow.steps.extend([
        SpatialInputRWS(name='Pick study area', order=1, help='Draw or select features for analysis.'),
        FormInputRWS(name='Configure inputs', order=2, help='Set parameters.'),
        SpatialCondorJobRWS(name='Run model', order=3, help='Submit the Condor job.'),
        ResultsResourceWorkflowStep(name='View results', order=4),
    ])

    session.add(workflow)
    session.commit()
    return workflow
```

The available step classes are listed on the [Resource Workflows concept page](../concepts/resource-workflows.md). Each step's `name`, `order`, and `help` strings show up in the workflow UI; subclass-specific options (e.g. allowed geometry types for `SpatialInputRWS`) live on the step instance.

## 3. Register the workflow router

```python
# my_first_app/app.py — register_url_maps
from tethysext.atcore.urls import resource_workflows as rw_urls
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter
from .models.workflows import AnalysisWorkflow


def register_url_maps(self):
    UrlMap = url_map_maker(self.root_url)

    return tuple(rw_urls.urls(
        url_map_maker=UrlMap,
        app=self,
        persistent_store_name='app_users_db',
        workflow_pairs=[(AnalysisWorkflow, ResourceWorkflowRouter)],
        base_template='my_first_app/base.html',
    ))
```

The router emits three URL maps per workflow type:

- `<workflow_type>_workflow`
- `<workflow_type>_workflow_step`
- `<workflow_type>_workflow_step_result`

## 4. Link a user into the workflow

```python
from django.shortcuts import redirect, reverse

return redirect(reverse(
    'my_first_app:analysis_workflow',
    kwargs={'resource_id': resource.id, 'workflow_id': workflow.id},
))
```

The router takes it from there — it loads the workflow, picks the current step (the first one not yet complete), and dispatches to the appropriate view from [`workflow_views`](../api/controllers/resource_workflows/workflow_views/index.mdx) or [`map_workflows`](../api/controllers/resource_workflows/map_workflows/index.mdx).

## 5. Customizing a step view

Subclass the appropriate view (e.g., [`SpatialInputMWV`](../api/controllers/resource_workflows/map_workflows/spatial_input_mwv.mdx) for `SpatialInputRWS`) and override `process_step_data` or `get_context`. Then subclass `ResourceWorkflowRouter` and add a mapping from your step class to your view, and pass _that_ subclass in the `workflow_pairs`.

:::caution Verification needed
The exact override mechanism for adding custom step-to-view mappings on `ResourceWorkflowRouter` (e.g. whether subclasses populate a class-level dict or override `_get_step_url_name` / `_get_step_view`) was not fully traced from the source. Confirm with the maintainers before customizing the router.
:::

## See also

- [Run a Condor Workflow Job](./run-a-condor-workflow-job.md) for `SpatialCondorJobRWS` specifics.
- [Permissions](../concepts/permissions.md) for `can_override_user_locks` (the workflow-lock override).
