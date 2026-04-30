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
- [`ResourceWorkflowStep`](../api/models/app_users/resource_workflow_step.mdx) — a single step. Steps are ordered, can reference other steps as parents, and carry their own status.
- [`ResourceWorkflowResult`](../api/models/app_users/resource_workflow_result.mdx) — output produced by a `ResultsResourceWorkflowStep`.

## Built-in step types

Concrete subclasses of `ResourceWorkflowStep`:

| Class | When to use it |
| --- | --- |
| [`SpatialInputRWS`](../api/models/resource_workflow_steps/spatial_input_rws.mdx) | Draw / edit features on a map. |
| [`SpatialAttributesRWS`](../api/models/resource_workflow_steps/spatial_attributes_rws.mdx) | Edit attributes of features added in a prior step. |
| [`SpatialDatasetRWS`](../api/models/resource_workflow_steps/spatial_dataset_rws.mdx) | Attach tabular datasets to spatial features. |
| [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx) | Submit a spatially-aware Condor job. |
| [`FormInputRWS`](../api/models/resource_workflow_steps/form_input_rws.mdx) | Plain Django form input driven by a `param.Parameterized` class. |
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

## The `new()` factory contract

Every `ResourceWorkflow` subclass in production atcore apps defines a `new()` classmethod with the same signature:

```python
class AnalysisWorkflow(ResourceWorkflow):
    TYPE = 'analysis'
    DISPLAY_TYPE_SINGULAR = 'Analysis'
    DISPLAY_TYPE_PLURAL = 'Analyses'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    @classmethod
    def new(cls, app, name, resource_id, creator_id,
            geoserver_name, map_manager, spatial_manager, **kwargs):
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id)

        step1 = SpatialInputRWS(
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

        step2 = SpatialCondorJobRWS(
            name='Run analysis',
            order=2,
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_jobs_callback,
                'workflow_kwargs': {'max_jobs': {'analysis': 4}},
                'working_message': 'Running analysis...',
                'error_message': 'Analysis failed.',
                'pending_message': 'Analysis pending.',
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )
        step2.parents.append(step1)

        step3 = ResultsResourceWorkflowStep(name='Results', order=3)
        step2.result = step3

        workflow.steps.extend([step1, step2, step3])
        return workflow
```

This contract is implicit but universal — the URL helpers and atcore's controllers pass `app`, `geoserver_name`, `map_manager`, and `spatial_manager` through to your factory when constructing a new workflow. Override the contract at your peril; following it makes your workflow a drop-in citizen.

### Why a factory and not just declared steps?

Steps need runtime values (the spatial manager configured for the request, the scheduler name, app-level options) that aren't available at class-definition time. The factory takes those in, builds the step graph in-memory, and returns the unsaved workflow. The caller commits.

## Step options patterns

The `options` dict on every step type is a mix of:

1. **Static config** — `'shapes': ['polygons']`, `'singular_name': 'Basin'`, `'allow_shapefile': True`.
2. **Callable values** — for things that need to evaluate at form-render or job-submit time, pass a function instead of a value:
   ```python
   options={
       'jobs': build_jobs_callback,           # SpatialCondorJobRWS
       'template_dataset': build_dataset_cb,  # SpatialDatasetRWS
       'plot_columns': build_columns_cb,      # SpatialDatasetRWS
   }
   ```
   The atcore step view calls these at the right moment with the live workflow context.
3. **Dot-path strings** for classes that should be lazily imported. `FormInputRWS.options['param_class']` and `XMSToolRWS.options['xmstool_class']` both accept a string like `'myapp_adapter.workflows.analysis.options.AnalysisOptions'` and import it on demand. This avoids a circular import when the form options module needs to import resource models that the workflow definition module also imports.
4. **Inter-step dependency declarations** — `SpatialDatasetRWS` reads from a parent step:
   ```python
   options={
       'geometry_source': {
           SpatialDatasetRWS.OPT_PARENT_STEP: {
               'match_attr': 'name',
               'match_value': 'Pick study area',
               'parent_field': 'geometry',
           },
       },
   }
   ```
   The `OPT_PARENT_STEP` key tells the step to fetch its geometry from a named parent step's output rather than asking the user to re-pick.

## Step authorization with `active_roles`

Pass `active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN]` to each step constructor to gate which app-user roles can see and execute it. This enables review-style workflows where the first three steps are user-facing and the last step is admin-only:

```python
review_step = SetStatusRWS(
    name='Review',
    order=4,
    active_roles=[Roles.ORG_REVIEWER, Roles.APP_ADMIN],
)
```

Combined with the workflow status state machine below, this is how multi-actor workflows are built.

## Connecting steps to results

A `SpatialCondorJobRWS` step that produces a results page wires it via the singular `result` attribute, not by appending to `workflow.results`:

```python
condor_step.result = results_step
workflow.steps.extend([..., condor_step, results_step])
```

The condor manager picks up `condor_step.result` when building `SpatialWorkflowResult` / `DatasetWorkflowResult` rows after the job finishes.

## Status progression

`ResourceWorkflow` defines a primary status progression and an optional review track:

```
Primary:
  PENDING -> CONTINUE -> WORKING -> COMPLETE
                      \-> ERROR / FAILED

Review (optional):
  SUBMITTED -> UNDER_REVIEW -> APPROVED / REJECTED / CHANGES_REQUESTED
                                                 -> REVIEWED
```

The status reflects the rolled-up state of the workflow's steps: `WORKING` if any step is processing, `ERROR` / `FAILED` if any step has errored, otherwise the lowest-severity status across steps.

## Controllers

The router is [`ResourceWorkflowRouter`](../api/controllers/resource_workflows/resource_workflow_router.mdx#resourceworkflowrouter). It dispatches each step to the right view based on the step's `CONTROLLER` attribute (a dot-path string pointing at a `ResourceWorkflowView` subclass). The base view is [`ResourceWorkflowView`](../api/controllers/resource_workflows/workflow_view.mdx). Concrete views live in:

- [`controllers.resource_workflows.workflow_views`](../api/controllers/resource_workflows/workflow_views/index.mdx) — non-spatial step views.
- [`controllers.resource_workflows.map_workflows`](../api/controllers/resource_workflows/map_workflows/index.mdx) — map-based step views.
- [`controllers.resource_workflows.results_views`](../api/controllers/resource_workflows/results_views/index.mdx) — result viewers.

Most apps subclass `ResourceWorkflowRouter` only to override `default_back_url(request, resource_id)` so the "back" link returns to a sensible app page (e.g., the resource's tabbed details).

## Custom step types

When the built-in step types don't fit, subclass an appropriate base step and bind it to a custom view via the `CONTROLLER` dot-path:

```python
# myapp_adapter/workflow_steps/ndvi_rws.py
from tethysext.atcore.models.app_users import SpatialResourceWorkflowStep

class NDVIRWS(SpatialResourceWorkflowStep):
    CONTROLLER = 'tethysapp.myapp.controllers.workflow_steps.ndvi_mwv.NDVIMWV'
    TYPE = 'ndvi_step'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

```python
# tethysapp/myapp/controllers/workflow_steps/ndvi_mwv.py
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from myapp_adapter.workflow_steps.ndvi_rws import NDVIRWS

class NDVIMWV(MapWorkflowView):
    template_name = 'myapp/workflow_steps/ndvi.html'
    valid_step_classes = [NDVIRWS]

    def process_step_data(self, request, session, step, ...):
        ...
```

Both ends — the `CONTROLLER` dot-path on the step *and* the `valid_step_classes` list on the view — must agree. The router uses `CONTROLLER` to dispatch; the view uses `valid_step_classes` to refuse to render against the wrong step type.

See [Add a custom workflow step type](../how-to/add-a-custom-workflow-step-type.md) for the full recipe.

## Wiring URLs

Use [`tethysext.atcore.urls.resource_workflows.urls`](../api/urls/resource_workflows.mdx) and pass `workflow_pairs` — `(WorkflowModel, RouterClass)` tuples:

```python
# example — app.py register_url_maps
from tethysext.atcore.urls import resource_workflows as rw_urls
from .controllers.workflows.my_router import MyWorkflowRouter
from myapp_adapter.workflows.analysis import AnalysisWorkflow

url_maps = rw_urls.urls(
    url_map_maker=UrlMap,
    app=self,
    persistent_store_name='primary_db',
    workflow_pairs=((AnalysisWorkflow, MyWorkflowRouter),),
    custom_models=(MyOrganization,),
    custom_permissions_manager=MyPermissionsManager,
    base_template='myapp/workflows_base.html',
)
```

Apps with several workflow types call `rw_urls.urls(...)` once per workflow class. While `workflow_pairs` is a tuple, production apps tend to make one call per workflow because the per-call options (`base_template`, `custom_models`, `custom_permissions_manager`) tend to vary per workflow surface.

## Behind the scenes

The router decorates step controllers with [`workflow_step_controller`](../api/services/resource_workflows/decorators.mdx) from [`tethysext.atcore.services.resource_workflows.decorators`](../api/services/resource_workflows/decorators.mdx), which loads the workflow and step from the URL kwargs into the view.

For step types that submit Condor jobs, see [Run a Condor Workflow Job](../how-to/run-a-condor-workflow-job.md).
