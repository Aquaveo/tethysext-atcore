---
id: how-to-add-a-custom-workflow-step-type
title: Add a Custom Workflow Step Type
sidebar_label: Add a custom workflow step type
sidebar_position: 8
---

# Add a custom workflow step type

The built-in step types ([`SpatialInputRWS`](../api/models/resource_workflow_steps/spatial_input_rws.mdx), [`FormInputRWS`](../api/models/resource_workflow_steps/form_input_rws.mdx), [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx), [`XMSToolRWS`](../api/models/resource_workflow_steps/xms_tool_rws.mdx), ...) cover most needs. When you need something they don't — a domain-specific computation, a custom QC check, a specialized chart — define your own step type and a matching view.

The example below is a "compute NDVI for the picked area" step.

## 1. Subclass a step base

Pick the closest existing base: [`SpatialResourceWorkflowStep`](../api/models/app_users/resource_workflow_step.mdx) for map-based interaction, `FormInputRWS` for plain forms, `SpatialCondorJobRWS` for Condor-backed work. Set `CONTROLLER` to the dot-path of the view that renders the step:

```python
# myapp_adapter/workflow_steps/ndvi_rws.py
from tethysext.atcore.models.app_users import SpatialResourceWorkflowStep


class NDVIRWS(SpatialResourceWorkflowStep):
    CONTROLLER = 'tethysapp.myapp.controllers.workflow_steps.ndvi_mwv.NDVIMWV'
    TYPE = 'ndvi_step'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

`CONTROLLER` is a string, not an import — atcore resolves it at request time. This dodges a circular import: the view in the Tethys package imports the step, and the step in the adapter package would otherwise need to import the view.

If the step has its own attribute schema, add accessors via `set_attribute` / `get_attribute`:

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

Pick the matching view base: [`MapWorkflowView`](../api/controllers/resource_workflows/map_workflows/index.mdx) for spatial steps, [`ResourceWorkflowView`](../api/controllers/resource_workflows/workflow_view.mdx) for non-spatial. Set `valid_step_classes` to the step types this view will render:

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
        # Anything the template needs beyond the base view.
        context['available_bands'] = ['B02', 'B03', 'B04', 'B08']
        return context

    def process_step_data(self, request, session, step, *args, **kwargs):
        # Read POSTed form data, validate, persist via step attributes.
        red = request.POST.get('red_band')
        if red:
            step.red_band = red
        # Returning super() lets atcore run its status transitions.
        return super().process_step_data(request, session, step, *args, **kwargs)
```

`valid_step_classes` is the safety check: if the router dispatches the wrong step type, the view raises instead of silently rendering against the wrong schema. The router dispatches by `CONTROLLER`; the view refuses by `valid_step_classes`. Keep the two in sync.

## 3. Provide the template

The custom view needs a template that extends the right atcore template. For a map-based step:

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

The atcore template handles the surrounding map, the layer toggle, and next/back navigation. Supply the form fields for your step.

## 4. Use the step in a workflow

Drop the step into a `ResourceWorkflow.new()` factory like any built-in step:

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

The router reads `NDVIRWS.CONTROLLER`, resolves it to `NDVIMWV`, and renders. No router subclass needed.

## 5. (Optional) Override the router only for navigation

To send the "back" link somewhere specific, subclass `ResourceWorkflowRouter` and override `default_back_url`:

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
