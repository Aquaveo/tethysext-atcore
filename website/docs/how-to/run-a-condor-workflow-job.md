---
id: how-to-run-a-condor-workflow-job
title: Run a Condor Workflow Job
sidebar_label: Run a Condor workflow job
sidebar_position: 5
---

# Run a Condor workflow job

atcore submits long-running jobs through HTCondor and updates the resource (or workflow step) status when they finish. There are two paths:

- [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx) — used when **creating** a `Resource` to run any required initialization jobs.
- [`ResourceWorkflowCondorJobManager`](../api/services/workflow_manager/condor_workflow_manager.mdx) — used inside a [Resource Workflow](../concepts/resource-workflows.md) to run jobs as a workflow step.

Both end up creating Tethys Condor workflow jobs. The difference is what they wire status updates back to.

## Resource initialization (one-time, on create)

Use this when a brand-new `Resource` needs setup before it's usable.

```python
# example — controllers/modify_project.py
from tethysext.atcore.services.resource_condor_workflow import ResourceCondorWorkflow
from tethys_sdk.jobs import CondorWorkflowJobNode

def submit_init(app, request, resource, scheduler, job_manager, workspace_path):
    rcw = ResourceCondorWorkflow(
        app=app,
        user=request.user,
        workflow_name=f'init-{resource.name}',
        workspace_path=workspace_path,
        resource_db_url=str(session.get_bind().url),
        resource=resource,
        scheduler=scheduler,
        job_manager=job_manager,
        status_keys=['init'],
    )
    # Override get_jobs() in a subclass to return your CondorWorkflowJobNode list.
    return rcw
```

`status_keys` lists the keys atcore will check on `resource.get_status(key)`. Your job script must set those statuses to one of [`Resource.OK_STATUSES`](../api/mixins/status_mixin.mdx) for the resource to flip from `STATUS_PENDING` to `STATUS_AVAILABLE`.

The helper script atcore ships for status updates is [`tethysext.atcore.job_scripts.update_resource_status`](https://github.com/Aquaveo/tethysext-atcore/blob/master/tethysext/atcore/job_scripts/update_resource_status.py) — Condor calls it when the workflow finishes.

## Workflow step jobs (`SpatialCondorJobRWS`)

When you reach a [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx) step in a workflow, atcore instantiates a `ResourceWorkflowCondorJobManager`:

```python
# example — inside a custom step view
from tethysext.atcore.services.workflow_manager.condor_workflow_manager import (
    ResourceWorkflowCondorJobManager,
)

manager = ResourceWorkflowCondorJobManager(
    session=session,
    resource=resource,
    resource_workflow_step=step,
    user=request.user,
    working_directory=app.get_app_workspace().path,
    app=app,
    scheduler_name='my-scheduler',
    jobs=[
        # CondorWorkflowJobNode instances or dicts describing them
    ],
    input_files=['/path/to/extra/input.csv'],
    gs_engine=app.get_spatial_dataset_service('gs', as_engine=True),
    resource_workflow=workflow,
)

manager.prepare()
manager.run_job()
```

The manager stamps each job with the IDs and class paths it needs to call back into the database:

- `resource_db_url`, `model_db_url`
- `resource_id`, `resource_workflow_id`, `resource_workflow_step_id`
- `gs_private_url`, `gs_public_url`
- `resource_class`, `workflow_class`

Your Condor job script receives those as positional arguments and is expected to update the workflow step's status when it finishes.

## Choosing where the workspace lives

Both managers create a workspace directory under `working_directory`. For step jobs, the layout is:

```
<working_directory>/<workflow_id>/<step_id>/<safe_job_name>/
```

`safe_job_name` is the step name with non-alphanumeric characters replaced by underscores.

## Custom job args

`ResourceWorkflowCondorJobManager` accepts `*args` after the keyword arguments — they're appended to `job_args` and forwarded to every job in the workflow. Use this to pass app-specific config (e.g., a model engine name) without subclassing.

:::tip
Use `use_atcore_args=False` on `CondorWorkflowJobNode` (recently added — see commit `ff2b495`) to opt-out of the standard atcore arg list when you need a job that doesn't read those positional arguments.
:::

## See also

- [Resource Workflows](../concepts/resource-workflows.md) for the surrounding workflow infrastructure.
- [Services](../concepts/services.md) for `ModelDatabase` (used to stamp `model_db_url` on the manager).
