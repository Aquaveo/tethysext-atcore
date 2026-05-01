---
id: how-to-build-a-resource-workflow
title: Build a Resource Workflow
sidebar_label: Build a resource workflow
sidebar_position: 2
---

# Build a resource workflow

Compose a custom workflow from the built-in step types, then register its URLs.

## 1. Subclass `ResourceWorkflow` with a `new()` factory

Define a `new()` classmethod that takes the runtime context (app, resource id, GeoServer name, map and spatial managers) and returns an unsaved workflow with its step graph populated. atcore's URL helpers and controllers expect this shape.

```python
# myapp_adapter/workflows/analysis.py
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps import (
    SpatialInputRWS, FormInputRWS, SpatialCondorJobRWS, ResultsResourceWorkflowStep,
)
from tethysext.atcore.services.app_users.roles import Roles


def build_jobs_callback(workflow, step, *args, **kwargs):
    """Returns the CondorWorkflowJobNode dict list for this run."""
    return []  # replace with real job specs


class AnalysisWorkflow(ResourceWorkflow):
    TYPE = 'analysis'
    DISPLAY_TYPE_SINGULAR = 'Analysis'
    DISPLAY_TYPE_PLURAL = 'Analyses'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    @classmethod
    def new(cls, app, name, resource_id, creator_id,
            geoserver_name, map_manager, spatial_manager, **kwargs):
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id)

        pick = SpatialInputRWS(
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

        configure = FormInputRWS(
            name='Configure inputs',
            order=2,
            options={
                # Dot-path string — the form module is imported lazily so it
                # can in turn import other domain models without circulars.
                'param_class': 'myapp_adapter.workflows.analysis.options.AnalysisOptions',
                'form_title': 'Analysis Options',
                'renderer': 'django',
            },
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )

        run = SpatialCondorJobRWS(
            name='Run analysis',
            order=3,
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_jobs_callback,         # callable, not a static list
                'workflow_kwargs': {},
                'working_message': 'Running...',
                'error_message': 'Failed.',
                'pending_message': 'Pending.',
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )
        run.parents.append(pick)

        results = ResultsResourceWorkflowStep(name='Results', order=4)
        run.result = results        # singular `result`, not `results.append`

        workflow.steps.extend([pick, configure, run, results])
        return workflow
```

Two bits of wiring beyond `workflow.steps.extend(...)`:

- `run.parents.append(pick)` declares that the condor step depends on the spatial-input step. Step views read `parents` to fetch upstream data (e.g., the polygon the user drew).
- `run.result = results` ties a job step to the page that displays its output. It's singular — don't append to `workflow.results`; the condor manager populates that list when the job finishes.

## 2. Build the form options class

`FormInputRWS.options['param_class']` is a dot-path string. atcore imports the class lazily after the workflow module finishes loading, so the form module can import other domain models without circulars:

```python
# myapp_adapter/workflows/analysis/options.py
import param


class AnalysisOptions(param.Parameterized):
    duration_days = param.Integer(default=30, bounds=(1, 365), doc='Analysis duration')
    include_uncertainty = param.Boolean(default=False)
```

atcore's `param_widgets` translate `param.Parameterized` fields into Django form fields.

## 3. Instantiate the workflow

Call `new()` from a controller or a Django shell:

```python
# example — controllers/start_analysis.py
from myapp_adapter.workflows.analysis import AnalysisWorkflow

workflow = AnalysisWorkflow.new(
    app=app,
    name=f'Analysis for {project.name}',
    resource_id=project.id,
    creator_id=request.user.username,
    geoserver_name='primary_geoserver',
    map_manager=map_manager,
    spatial_manager=spatial_manager,
)
session.add(workflow)
session.commit()
```

## 4. Register the workflow router

```python
# myapp/app.py — register_url_maps
from tethysext.atcore.urls import resource_workflows as rw_urls
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter
from myapp_adapter.workflows.analysis import AnalysisWorkflow


def register_url_maps(self):
    UrlMap = url_map_maker(self.root_url)

    return tuple(rw_urls.urls(
        url_map_maker=UrlMap,
        app=self,
        persistent_store_name='primary_db',
        workflow_pairs=((AnalysisWorkflow, ResourceWorkflowRouter),),
        base_template='myapp/workflows_base.html',
    ))
```

The router emits three URL maps per workflow type:

- `<workflow_type>_workflow`
- `<workflow_type>_workflow_step`
- `<workflow_type>_workflow_step_result`

Call `rw_urls.urls(...)` once per workflow type. The per-call options (template, custom models, permissions manager) usually differ.

## 5. Link a user into the workflow

```python
from django.shortcuts import redirect, reverse

return redirect(reverse(
    'myapp:analysis_workflow',
    kwargs={'resource_id': resource.id, 'workflow_id': workflow.id},
))
```

The router loads the workflow, picks the current step (the first one not yet complete), and dispatches to the appropriate view from [`workflow_views`](../api/controllers/resource_workflows/workflow_views/index.mdx) or [`map_workflows`](../api/controllers/resource_workflows/map_workflows/index.mdx).

## 6. Customizing a step view

Subclass the view for your step base, override the hook you need, and point the step's `CONTROLLER` attribute (a dot-path string) at the subclass.

```python
# myapp/controllers/workflow_steps/picky_spatial_input_mwv.py
from tethysext.atcore.controllers.resource_workflows.map_workflows import (
    SpatialInputMWV,
)


class PickyspatialInputMWV(SpatialInputMWV):
    template_name = 'myapp/workflow_steps/picky_spatial_input.html'

    def process_step_data(self, request, session, step, *args, **kwargs):
        # Validate, transform, or augment the submitted features here.
        return super().process_step_data(request, session, step, *args, **kwargs)
```

Set `CONTROLLER` on the step type to the dot-path of the view:

```python
# myapp_adapter/workflow_steps/picky_spatial_input_rws.py
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS


class PickySpatialInputRWS(SpatialInputRWS):
    CONTROLLER = 'myapp.controllers.workflow_steps.picky_spatial_input_mwv.PickyspatialInputMWV'
    TYPE = 'picky_spatial_input'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

The router dispatches each step via `CONTROLLER`. There's no class-level dict to populate on `ResourceWorkflowRouter`, and you don't need to subclass the router unless you want to override behavior like `default_back_url(request, resource_id)`.

For defining a new step base or attribute schema, see [Add a custom workflow step type](./add-a-custom-workflow-step-type.md).

## See also

- [Resource Workflows concept page](../concepts/resource-workflows.md) — the `new()` factory contract and step-options patterns.
- [Run a Condor Workflow Job](./run-a-condor-workflow-job.md) — `SpatialCondorJobRWS` specifics.
- [Permissions](../concepts/permissions.md) — `can_override_user_locks` (the workflow-lock override).
