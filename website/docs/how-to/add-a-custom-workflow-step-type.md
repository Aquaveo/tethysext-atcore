---
id: how-to-add-a-custom-workflow-step-type
title: Add a Custom Workflow Step Type
sidebar_label: Add a custom workflow step type
sidebar_position: 8
---

# Add a custom workflow step type

The built-in step types ([`SpatialInputRWS`](../api/models/resource_workflow_steps/spatial_input_rws.mdx), [`FormInputRWS`](../api/models/resource_workflow_steps/form_input_rws.mdx), [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx), [`XMSToolRWS`](../api/models/resource_workflow_steps/xms_tool_rws.mdx), ...) cover most needs. When you need a step that does something atcore doesn't ship — a domain-specific NDVI computation, a custom mesh-quality check, a specialized chart — define your own step type and a matching view.

This recipe takes a "compute NDVI for the picked area" step as a running example.

## 1. Subclass a step base

Pick the closest existing base. For map-based interaction use [`SpatialResourceWorkflowStep`](../api/models/app_users/resource_workflow_step.mdx); for plain forms use `FormInputRWS`; for Condor-backed work use `SpatialCondorJobRWS`. Set `CONTROLLER` to the dot-path of the view that will render the step:

```python
# myapp_adapter/workflow_steps/ndvi_rws.py
from tethysext.atcore.models.app_users import SpatialResourceWorkflowStep


class NDVIRWS(SpatialResourceWorkflowStep):
    CONTROLLER = 'tethysapp.myapp.controllers.workflow_steps.ndvi_mwv.NDVIMWV'
    TYPE = 'ndvi_step'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

`CONTROLLER` is a string, not an import — atcore resolves it at request time. This avoids a circular import (the view in the Tethys package needs to import the step; the step in the adapter package would otherwise need to import the view).

If your step has its own attribute schema, add `param.Parameterized` accessors via `set_attribute` / `get_attribute`:

```python
class NDVIRWS(SpatialResourceWorkflowStep):
    CONTROLLER = 'tethysapp.myapp.controllers.workflow_steps.ndvi_mwv.NDVIMWV'
    TYPE = 'ndvi_step'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    @property
    def red_band(self):
        return self.get_attribute('red_band', 'B04')

    @red_band.setter
    def red_band(self, value):
        self.set_attribute('red_band', value)
```

## 2. Subclass a workflow view

Pick the matching view base — [`MapWorkflowView`](../api/controllers/resource_workflows/map_workflows/index.mdx) for spatial steps, [`ResourceWorkflowView`](../api/controllers/resource_workflows/workflow_view.mdx) for non-spatial — and set `valid_step_classes` to the list of step types this view is willing to render:

```python
# tethysapp/myapp/controllers/workflow_steps/ndvi_mwv.py
from tethys_sdk.gizmos import MapView, MVLayer
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from myapp_adapter.workflow_steps.ndvi_rws import NDVIRWS


class NDVIMWV(MapWorkflowView):
    template_name = 'myapp/workflow_steps/ndvi.html'
    valid_step_classes = [NDVIRWS]

    def get_context(self, request, session, resource, context, *args, **kwargs):
        context = super().get_context(request, session, resource, context, *args, **kwargs)
        # Add anything the template needs beyond what the base view provides.
        context['available_bands'] = ['B02', 'B03', 'B04', 'B08']
        return context

    def process_step_data(self, request, session, step, *args, **kwargs):
        # Read POSTed form data, validate, persist via step attributes.
        red = request.POST.get('red_band')
        if red:
            step.red_band = red
        # Returning the result of super() lets atcore's status transitions run.
        return super().process_step_data(request, session, step, *args, **kwargs)
```

The `valid_step_classes` list is the safety check: if the router accidentally dispatches the wrong step type to this view, it raises rather than silently rendering against the wrong schema.

The `CONTROLLER` dot-path on the step *and* `valid_step_classes` on the view must agree. The router uses `CONTROLLER` to dispatch; the view uses `valid_step_classes` to refuse to render against the wrong step type.

## 3. Provide the template

Custom step views need a template that extends the appropriate atcore template. For a map-based step:

```html
{# tethysapp/myapp/templates/myapp/workflow_steps/ndvi.html #}
{% extends 'atcore/resource_workflows/spatial_workflow_view.html' %}

{% block step_form_inputs %}
  <div class="mb-3">
    <label class="form-label">Red band</label>
    <select name="red_band" class="form-select">
      {% for band in available_bands %}
        <option value="{{ band }}" {% if band == step.red_band %}selected{% endif %}>
          {{ band }}
        </option>
      {% endfor %}
    </select>
  </div>
{% endblock %}
```

The atcore template provides the surrounding map, the layer toggle, and the next/back navigation; you just supply the form fields specific to your step.

## 4. Use the step in a workflow

Once the step type is defined, drop it into a `ResourceWorkflow.new()` factory like any built-in step:

```python
# myapp_adapter/workflows/vegetation/__init__.py
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.services.app_users.roles import Roles
from myapp_adapter.workflow_steps.ndvi_rws import NDVIRWS


class VegetationWorkflow(ResourceWorkflow):
    TYPE = 'vegetation'
    DISPLAY_TYPE_SINGULAR = 'Vegetation Analysis'
    DISPLAY_TYPE_PLURAL = 'Vegetation Analyses'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    @classmethod
    def new(cls, app, name, resource_id, creator_id,
            geoserver_name, map_manager, spatial_manager, **kwargs):
        wf = cls(name=name, resource_id=resource_id, creator_id=creator_id)
        ndvi = NDVIRWS(
            name='Compute NDVI',
            order=1,
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[Roles.ORG_USER, Roles.ORG_ADMIN],
        )
        wf.steps.append(ndvi)
        return wf
```

The router reads `NDVIRWS.CONTROLLER`, resolves the dot-path to `NDVIMWV`, and renders. No router subclass needed.

## 5. (Optional) Override the router only for navigation

If you want the "back" link to land somewhere specific, subclass `ResourceWorkflowRouter` and override `default_back_url`:

```python
# tethysapp/myapp/controllers/workflows/my_router.py
from django.urls import reverse
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowRouter


class MyWorkflowRouter(ResourceWorkflowRouter):
    def default_back_url(self, request, resource_id, *args, **kwargs):
        return reverse('myapp:project_details_tab', kwargs={
            'resource_id': resource_id,
            'tab_slug': 'workflows',
        })
```

Pair it with the workflow class in `rw_urls.urls(workflow_pairs=((VegetationWorkflow, MyWorkflowRouter),))`.

## See also

- [Build a Resource Workflow](./build-a-resource-workflow.md) for the surrounding workflow recipe.
- [Resource Workflows concept](../concepts/resource-workflows.md#custom-step-types).
