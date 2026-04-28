---
id: concepts-resource-workflows
title: Resource Workflows
sidebar_label: Resource Workflows
sidebar_position: 4
---

# Resource workflows

A `ResourceWorkflow` is a stateful, multi-step process attached to a `Resource`. Use it to walk a user through wizard-style sequences (configure inputs, pick a region, submit a job, view results) with persistent intermediate state and authorization.

## Pieces

The data model is in [`tethysext.atcore.models.app_users`](../api/models/app_users/index.mdx) and [`tethysext.atcore.models.resource_workflow_steps`](../api/models/resource_workflow_steps/index.mdx):

- [`ResourceWorkflow`](../api/models/app_users/resource_workflow.mdx#resourceworkflow) — the parent record. References its `Resource` and `creator` (`AppUser`), and owns ordered `steps` and `results`.
- [`ResourceWorkflowStep`](../api/models/app_users/resource_workflow_step.mdx) — a single step. Steps are ordered, can reference results, and carry their own status.
- [`ResourceWorkflowResult`](../api/models/app_users/resource_workflow_result.mdx) — output produced by a step.

## Built-in step types

Concrete subclasses of `ResourceWorkflowStep`:

| Class | When to use it |
| --- | --- |
| [`SpatialInputRWS`](../api/models/resource_workflow_steps/spatial_input_rws.mdx) | Draw / edit features on a map. |
| [`SpatialAttributesRWS`](../api/models/resource_workflow_steps/spatial_attributes_rws.mdx) | Edit attributes of features added in a prior step. |
| [`SpatialDatasetRWS`](../api/models/resource_workflow_steps/spatial_dataset_rws.mdx) | Attach tabular datasets to spatial features. |
| [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx) | Submit a spatially-aware Condor job. |
| [`FormInputRWS`](../api/models/resource_workflow_steps/form_input_rws.mdx) | Plain Django form input. |
| [`TableInputRWS`](../api/models/resource_workflow_steps/table_input_rws.mdx) | Tabular input (rows of typed cells). |
| [`XMSToolRWS`](../api/models/resource_workflow_steps/xms_tool_rws.mdx) | Run an XMS Tool against the workflow inputs. |
| [`SetStatusRWS`](../api/models/resource_workflow_steps/set_status_rws.mdx) | Manually transition the workflow status (e.g. submit-for-review). |
| [`ResultsResourceWorkflowStep`](../api/models/resource_workflow_steps/results_rws.mdx) | Display generated results. |

## Built-in result types

Found in [`tethysext.atcore.models.resource_workflow_results`](../api/models/resource_workflow_results/index.mdx):

- [`SpatialWorkflowResult`](../api/models/resource_workflow_results/spatial_workflow_result.mdx) — map layers and features.
- [`DatasetWorkflowResult`](../api/models/resource_workflow_results/dataset_workflow_result.mdx) — tabular data.
- [`PlotWorkflowResult`](../api/models/resource_workflow_results/plot_workflow_result.mdx) — Plotly / Bokeh plots.
- [`ReportWorkflowResult`](../api/models/resource_workflow_results/report_workflow_result.mdx) — multi-section reports composed from the others.

## Status progression

`ResourceWorkflow` defines a primary status progression and an optional review track. From the class docstring:

```
Primary:
  PENDING -> CONTINUE -> WORKING -> COMPLETE
                      \-> ERROR / FAILED

Review (optional):
  SUBMITTED -> UNDER_REVIEW -> APPROVED / REJECTED / CHANGES_REQUESTED
```

The status reflects the rolled-up state of the workflow's steps: `WORKING` if any step is processing, `ERROR` / `FAILED` if any step has errored, otherwise the lowest-severity status across steps.

## Controllers

The router is [`ResourceWorkflowRouter`](../api/controllers/resource_workflows/resource_workflow_router.mdx#resourceworkflowrouter). It dispatches each step to the right view based on the step's class. The base view is [`ResourceWorkflowView`](../api/controllers/resource_workflows/workflow_view.mdx). Concrete views live in:

- [`controllers.resource_workflows.workflow_views`](../api/controllers/resource_workflows/workflow_views/index.mdx) — non-spatial step views.
- [`controllers.resource_workflows.map_workflows`](../api/controllers/resource_workflows/map_workflows/index.mdx) — map-based step views.
- [`controllers.resource_workflows.results_views`](../api/controllers/resource_workflows/results_views/index.mdx) — result viewers.

## Wiring URLs

Use [`tethysext.atcore.urls.resource_workflows.urls`](../api/urls/resource_workflows.mdx) and pass `workflow_pairs` — `(WorkflowModel, RouterClass)` tuples:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import resource_workflows as rw_urls
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter
from .models.workflows import MyAnalysisWorkflow

url_maps = rw_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='app_users_db',
    workflow_pairs=[(MyAnalysisWorkflow, ResourceWorkflowRouter)],
    base_template='my_first_app/base.html',
)
```

The handler argument defaults to [`panel_rws_handler`](../api/handlers.mdx) for Bokeh-based step types.

## Behind the scenes

The router decorates step controllers with [`workflow_step_controller`](../api/services/resource_workflows/decorators.mdx) from [`tethysext.atcore.services.resource_workflows.decorators`](../api/services/resource_workflows/decorators.mdx), which loads the workflow and step from the URL kwargs into the view.

For step types that submit Condor jobs, see [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md).
