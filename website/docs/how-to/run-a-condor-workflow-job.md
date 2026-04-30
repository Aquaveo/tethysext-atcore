---
id: how-to-run-a-condor-workflow-job
title: Run a Condor Workflow Job
sidebar_label: Run a Condor workflow job
sidebar_position: 5
---

# Run a Condor workflow job

atcore submits long-running jobs through HTCondor and updates the resource (or workflow step) status when they finish. There are two paths:

- [`ResourceCondorWorkflow`](../api/services/resource_condor_workflow.mdx) — used when **creating** a `Resource` to run any required initialization jobs.
- [`ResourceWorkflowCondorJobManager`](../api/services/workflow_manager/condor_workflow_manager.mdx) — used inside a [Resource Workflow](../concepts/resource-workflows.md) to run jobs as a `SpatialCondorJobRWS` step.

Both end up creating Tethys Condor workflow jobs. The difference is what they wire status updates back to.

## Resource initialization (one-time, on create)

Use this when a brand-new `Resource` needs setup before it's usable.

```python
# example — controllers/modify_project.py
from tethysext.atcore.services.resource_condor_workflow import ResourceCondorWorkflow

def submit_init(app, request, resource, scheduler, job_manager, workspace_path, session):
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

When you reach a [`SpatialCondorJobRWS`](../api/models/resource_workflow_steps/spatial_condor_job_rws.mdx) step in a workflow, atcore instantiates a `ResourceWorkflowCondorJobManager` automatically. The integration point is the **`jobs` callable** you put on the step's `options` dict.

### The `jobs` callback pattern

`SpatialCondorJobRWS.options['jobs']` is a callable, not a static list. atcore invokes it at submit time, passing the live workflow context. The callback returns a list of dicts that map to `condorpy_template_name` job specs.

```python
# myapp_adapter/workflows/analysis/jobs.py
import os


def build_jobs_callback(workflow, step, *args, **kwargs):
    """Build the CondorWorkflowJobNode dict list for this run.

    Called at submit time so the callback can read the latest workflow
    state (e.g., form-input values from upstream FormInputRWS steps).
    """
    # Pull upstream form input via the parents the step declares.
    form_step = next(p for p in step.parents if p.name == 'Configure inputs')
    options = form_step.get_attribute('form-values') or {}

    job_executable_dir = os.path.dirname(__file__)

    return [
        {
            'name': 'run_analysis',
            'condorpy_template_name': 'vanilla_transfer_files',
            'attributes': {
                'executable': os.path.join(job_executable_dir, 'run_analysis.py'),
                'transfer_input_files': '($transfer_input_files)',
                'transfer_output_files': 'results.json,output.tif',
            },
            'remote_input_files': [],
            'remote_output_files': ['results.json', 'output.tif'],
        },
    ]
```

Wire it onto the step in your `ResourceWorkflow.new()` factory:

```python
SpatialCondorJobRWS(
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
```

### What atcore stamps onto each job

`ResourceWorkflowCondorJobManager` automatically appends a positional argument list to every job in the workflow. Your job script receives them as `sys.argv`:

```
resource_db_url, model_db_url,
resource_id, resource_workflow_id, resource_workflow_step_id,
gs_private_url, gs_public_url,
resource_class, workflow_class,
... any extra positional args you passed ...
```

Use `tethysext.atcore.job_scripts.update_resource_status` from your job script to write status back to the workflow step:

```python
#!/usr/bin/env python
# myapp_adapter/job_scripts/run_analysis.py
import sys
from tethysext.atcore.job_scripts.update_resource_status import update_resource_status


def main():
    args = sys.argv[1:]
    resource_db_url = args[0]
    resource_workflow_step_id = args[4]

    try:
        # ... do the actual work, write outputs ...
        status = 'STATUS_COMPLETE'
    except Exception:
        status = 'STATUS_ERROR'

    update_resource_status(
        resource_db_url=resource_db_url,
        resource_workflow_step_id=resource_workflow_step_id,
        status=status,
    )


if __name__ == '__main__':
    main()
```

### Opting out of the standard arg list

If your job is generic (e.g., wraps a third-party CLI) and shouldn't read those positional arguments, set `use_atcore_args=False` on the `CondorWorkflowJobNode` in your jobs callback. The job will be submitted without atcore's stamped args, and you're responsible for status updates yourself.

## Calling the manager directly

If you need to submit a Condor workflow outside the `SpatialCondorJobRWS` flow (rare), the manager is callable:

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
    scheduler_name=app.SCHEDULER_NAME,
    jobs=build_jobs_callback(workflow, step),
    input_files=[],
    gs_engine=app.get_spatial_dataset_service('primary_geoserver', as_engine=True),
    resource_workflow=workflow,
)

manager.prepare()
manager.run_job()
```

## Choosing where the workspace lives

Both managers create a workspace directory under `working_directory`. For step jobs, the layout is:

```
<working_directory>/<workflow_id>/<step_id>/<safe_job_name>/
```

`safe_job_name` is the step name with non-alphanumeric characters replaced by underscores.

## See also

- [Resource Workflows](../concepts/resource-workflows.md) for the surrounding workflow infrastructure.
- [Services](../concepts/services.md) for `ModelDatabase` (used to stamp `model_db_url` on the manager).
