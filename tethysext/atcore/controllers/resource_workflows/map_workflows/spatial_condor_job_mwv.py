"""
********************************************************************************
* Name: spatial_input_mwv.py
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import json
import logging
from django.contrib import messages
from django.shortcuts import render, redirect
from tethys_sdk.gizmos import JobsTable
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS
from tethysext.atcore.services.resource_workflows.helpers import initialize_step_statuses
from tethysext.atcore.services.workflow_manager.condor_workflow_manager import ResourceWorkflowCondorJobManager


log = logging.getLogger(f'tethys.{__name__}')


class SpatialCondorJobMWV(MapWorkflowView):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_condor_job_mwv.html'
    valid_step_classes = [SpatialCondorJobRWS]
    previous_steps_selectable = True
    jobs_table_refresh_interval = int(os.getenv('JOBS_TABLE_REFRESH_INTERVAL', 30000))  # ms

    def process_step_options(self, request, session, context, resource, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            resource(Resource): the resource for this request.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
        # Turn off feature selection on model layers
        map_view = context['map_view']
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Can run workflows if not readonly
        can_run_workflows = not self.is_read_only(request, current_step)

        # get tabular data if any
        tabular_data = current_step.workflow.get_tabular_data_for_previous_steps(current_step, request, session,
                                                                                 resource)

        has_tabular_data = len(tabular_data) > 0

        # Preprocess tabular data
        def format_as_html_list(data):
            text = "<ul>"
            for k, v in data.items():
                if isinstance(v, dict):
                    text += f'<li><b>{k}</b>:</li>'
                    text += format_as_html_list(v)
                else:  # this else block can be removed if you don't need it
                    text += f'<li><b>{k}</b>: {v}</li>'
            text += "</ul>"
            return text

        # Preprocess each parameter value as needed
        for step_name, parameters in tabular_data.items():
            if not isinstance(parameters, dict):
                continue

            for parameter, parameter_value in parameters.items():
                # Tables handled in template
                if parameter == 'table':
                    continue
                # Recursively format nested dictionaries as html lists
                elif isinstance(parameter_value, dict):
                    tabular_data[step_name][parameter] = format_as_html_list(parameter_value)

        # get geometry data for previous steps
        geometry_data = MapWorkflowView.get_geometry_data_for_previous_steps(current_step)
        has_geometry_data = len(geometry_data) > 0

        # Save changes to map view and layer groups
        context.update({
            'can_run_workflows': can_run_workflows,
            'has_tabular_data': has_tabular_data,
            'tabular_data': tabular_data,
            'has_geometry_data': has_geometry_data
        })

        # Note: new layer created by super().process_step_options will have feature selection enabled by default
        super().process_step_options(
            request=request,
            session=session,
            context=context,
            resource=resource,
            current_step=current_step,
            previous_step=previous_step,
            next_step=next_step
        )

    def on_get_step(self, request, session, resource, workflow, current_step, previous_step, next_step,
                    *args, **kwargs):
        """
        Hook that is called at the beginning of the get request for a workflow step, before any other controller logic occurs.
            request(HttpRequest): The request.
            session(sqlalchemy.Session): the session.
            resource(Resource): the resource for this request.
            workflow(ResourceWorkflow): The current workflow.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        Returns:
            None or HttpResponse: If an HttpResponse is returned, render that instead.
        """  # noqa: E501
        step_status = current_step.get_status()
        if step_status != current_step.STATUS_PENDING:
            return self.render_condor_jobs_table(
                request, session, resource, workflow, current_step, previous_step, next_step
            )

    def render_condor_jobs_table(self, request, session, resource, workflow, current_step, previous_step, next_step):
        """
        Render a condor jobs table showing the status of the current job that is processing.
            request(HttpRequest): The request.
            session(sqlalchemy.Session): the session.
            resource(Resource): the resource for this request.
            workflow(ResourceWorkflow): The current workflow.
            current_step(ResourceWorkflowStep): The current step to be rendered.
        Returns:
            HttpResponse: The condor job table view.
        """
        job_id = current_step.get_attribute('condor_job_id')
        app = self.get_app()
        job_manager = app.get_job_manager()
        step_job = job_manager.get_job(job_id=job_id)
        app_user = self._AppUser.get_app_user_from_request(request, session)
        show_job_table_actions = app_user.is_staff() or app_user.get_role() in [
            self._AppUser.ROLES.APP_ADMIN,
            self._AppUser.ROLES.ORG_ADMIN
        ]

        jobs_table = JobsTable(
            jobs=[step_job],
            column_fields=('description', 'creation_time', ),
            hover=True,
            striped=True,
            condensed=False,
            show_status=True,
            show_detailed_status=True,
            actions=['logs'],
            show_actions=show_job_table_actions,
            refresh_interval=self.jobs_table_refresh_interval,
        )

        # Build step cards
        steps = self.build_step_cards(request, workflow)

        # Get the current app
        step_url_name = self.get_step_url_name(request, workflow)

        # Can run workflows if not readonly
        can_run_workflows = not self.is_read_only(request, current_step)

        # Configure workflow lock display
        lock_display_options = self.build_lock_display_options(request, workflow)

        context = {
            'resource': resource,
            'workflow': workflow,
            'steps': steps,
            'current_step': current_step,
            'next_step': next_step,
            'previous_step': previous_step,
            'step_url_name': step_url_name,
            'next_title': self.next_title,
            'finish_title': self.finish_title,
            'previous_title': self.previous_title,
            'back_url': self.back_url,
            'nav_title': '{}: {}'.format(resource.name, workflow.name),
            'nav_subtitle': workflow.DISPLAY_TYPE_SINGULAR,
            'jobs_table': jobs_table,
            'can_run_workflows': can_run_workflows,
            'lock_display_options': lock_display_options,
            'base_template': self.base_template
        }

        return render(request, 'atcore/resource_workflows/spatial_condor_jobs_table.html', context)

    def process_step_data(self, request, session, step, resource, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            step(ResourceWorkflowStep): The step to be updated.
            resource(Resource): The resource for this request.
            current_url(str): URL to step.
            previous_url(str): URL to the previous step.
            next_url(str): URL to the next step.

        Returns:
            HttpResponse: A Django response.

        Raises:
            ValueError: exceptions that occur due to user error, provide helpful message to help user solve issue.
            RuntimeError: exceptions that require developer attention.
        """  # noqa: E501
        if 'next-submit' in request.POST:
            step.validate()

            status = step.get_status(step.ROOT_STATUS_KEY)

            if status != step.STATUS_COMPLETE:
                if status == step.STATUS_WORKING:
                    working_message = step.options.get(
                        'working_message',
                        'Please wait for the job to finish running before proceeding.'
                    )
                    messages.warning(request, working_message)
                elif status in (step.STATUS_ERROR, step.STATUS_FAILED):
                    error_message = step.options.get(
                        'error_message',
                        'The job did not finish successfully. Please press "Rerun" to try again.'
                    )
                    messages.error(request, error_message)
                else:
                    pending_message = step.options.get(
                        'pending_message',
                        'Please press "Run" to continue.'
                    )
                    messages.info(request, pending_message)

                return redirect(request.path)

        return super().process_step_data(request, session, step, resource, current_url, previous_url, next_url)

    def run_job(self, request, session, resource, workflow_id, step_id, *args, **kwargs):
        """
        Handle run-job-form requests: prepare and submit the condor job.
        """
        if 'run-submit' not in request.POST and 'rerun-submit' not in request.POST:
            return redirect(request.path)

        # Get the workflow from the id
        workflow = self.get_workflow(request, workflow_id, session)

        # Validate data if going to next step
        step = self.get_step(request, step_id, session)

        if self.is_read_only(request, step):
            messages.warning(request, 'You do not have permission to run this workflow.')
            return redirect(request.path)

        # Get options
        scheduler_name = step.options.get('scheduler', None)
        if not scheduler_name:
            raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "scheduler" option supplied.')

        jobs = step.options.get('jobs', None)
        if not jobs:
            raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "jobs" option supplied.')

        workflow_kwargs = step.options.get('workflow_kwargs', None)

        # Get map manager
        map_manager = self.get_map_manager(request, resource)

        # Get GeoServer Connection Information
        gs_engine = map_manager.spatial_manager.gs_engine

        # Define the working directory
        app = self.get_app()
        working_directory = self.get_working_directory(request, app)

        # Setup the Condor Workflow
        condor_job_manager = ResourceWorkflowCondorJobManager(
            session=session,
            resource=resource,
            resource_workflow_step=step,
            jobs=jobs,
            user=request.user,
            working_directory=working_directory,
            app=app,
            scheduler_name=scheduler_name,
            gs_engine=gs_engine,
            resource_workflow=workflow,
            workflow_kwargs=workflow_kwargs,
        )

        # Delete the previous condor job first so its pre_delete signal doesn't remove the new workspace
        previous_condor_job_id = step.get_attribute('condor_job_id')
        if previous_condor_job_id:
            previous_job = app.get_job_manager().get_job(job_id=previous_condor_job_id)
            if previous_job:
                previous_job.delete()
            # Restore CWD to working_directory in case condorpy's @set_cwd left it pointing
            # to the now-deleted workspace (condor_workflow_pre_delete calls close_remote which
            # uses @set_cwd; if that leaves CWD in the old workspace, os.getcwd() will fail
            # when condorpy tries to submit the new job)
            os.chdir(working_directory)

        # Serialize parameters from all previous steps into json
        serialized_params = self.serialize_parameters(step)

        # Write serialized params to file for transfer
        params_file_path = os.path.join(condor_job_manager.workspace, 'workflow_params.json')
        with open(params_file_path, 'w') as params_file:
            params_file.write(serialized_params)

        # Add parameter file to workflow input files
        condor_job_manager.input_files.append(params_file_path)

        # Prepare the job
        job_id = condor_job_manager.prepare()

        # Deal with locking
        self.handle_on_submit_locking(request, session, resource, step)

        # Kept so the step can be put back if the submission below never happens.
        previous_status = step.get_status(step.ROOT_STATUS_KEY)
        previous_status_message = step.get_attribute(step.ATTR_STATUS_MESSAGE)

        # Update status of the resource workflow step
        step.set_status(step.ROOT_STATUS_KEY, step.STATUS_WORKING)
        step.set_attribute(step.ATTR_STATUS_MESSAGE, None)

        # Save the job id to the step for later reference
        step.set_attribute('condor_job_id', job_id)

        # Allow the step to track statuses on each "sub-job", keyed by node name.
        # This has to be committed BEFORE the job is submitted: nodes start
        # reporting as soon as DAGMan schedules them, and this write is an
        # unlocked overwrite of the whole attributes document, so clearing it
        # afterwards would discard statuses that had already been committed.
        initialize_step_statuses(step)

        session.commit()

        # Submit job
        submission_error = None

        try:
            condor_job_manager.run_job()
        except Exception as e:
            submission_error = e

        # A raised exception is not the only way submission fails, and is not even the
        # usual one: TethysJob.execute() catches everything the submit raises and records
        # the job as ERR instead, so run_job() returns normally after a scheduler that
        # could not be reached. The recorded status has to be checked as well.
        if submission_error is None and not self.job_was_submitted(condor_job_manager):
            submission_error = RuntimeError(
                'The job for step {} was not accepted by the scheduler.'.format(step.id)
            )

        if submission_error is not None:
            self.restore_step_after_failed_submission(
                session, step, previous_status, previous_status_message,
            )
            raise submission_error

        # Reset next steps only now that the job is really running. Doing it before
        # submission would discard downstream results for a run that never started.
        step.workflow.reset_next_steps(step)
        session.commit()

        return redirect(request.path)

    @staticmethod
    def job_was_submitted(condor_job_manager):
        """
        Whether the scheduler actually accepted the job.

        TethysJob.execute() wraps the submit in a bare except that records the job as
        ERR rather than re-raising, so the absence of an exception says nothing about
        whether submission happened.

        A recorded ERR is not conclusive either. CondorBase._execute() submits and then
        saves in two steps::

            self.cluster_id = self.condor_object.submit(*args, **kwargs)
            self.save()

        and both are inside that same bare except, so a save that fails after a submit
        that succeeded is recorded exactly like a scheduler that refused the job. Telling
        the caller that a running DAG was never submitted is the more expensive mistake:
        it would orphan the job and let the step's status document be rewritten without
        the row lock every reporting node takes. The cluster id is assigned before the
        save that can fail, so a non-zero value means the job is out there regardless of
        what the status says.

        Args:
            condor_job_manager(ResourceWorkflowCondorJobManager): The manager used to submit.

        Returns:
            bool: False only when the job is known not to be running.
        """
        workflow = getattr(condor_job_manager, 'workflow', None)

        if getattr(workflow, 'cluster_id', 0):
            return True

        # A missing workflow is not evidence of a failed submission. The manager
        # initialises it to None and only populates it in prepare(), which run_job()
        # always runs first, so None here means preparation did not happen rather than
        # that the scheduler refused anything. Reporting failure for it would raise on
        # paths that never attempted a submission at all.
        return getattr(workflow, '_status', None) not in ('ERR', 'ABT')

    @staticmethod
    def restore_step_after_failed_submission(session, step, previous_status, previous_status_message):
        """
        Undoes the pre-submission state when no job will ever report against it.

        Without this the step sits in WORKING waiting on a job that was never submitted,
        and the view refuses to let the user advance.

        Failure to restore is logged rather than raised: the caller is about to raise the
        submission error, and replacing it with a cleanup error would hide the real cause.
        """
        try:
            step.set_status(step.ROOT_STATUS_KEY, previous_status or step.STATUS_PENDING)
            step.set_attribute(step.ATTR_STATUS_MESSAGE, previous_status_message)
            step.set_attribute('condor_job_id', None)
            initialize_step_statuses(step)
            session.commit()
        except Exception:
            session.rollback()
            log.exception(
                'Could not restore step %s after a failed job submission; it may be left in %s.',
                step.id, step.STATUS_WORKING,
            )

    def handle_on_submit_locking(self, request, session, resource, step):
        """
        Acquires or releases the workflow or resource lock based on the step options.

        Args:
            request(HttpRequest): Django request instance.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            step(ResourceWorkflowStep): the step.
        """
        lock_workflow_on_submit = step.options.get('lock_workflow_on_job_submit', False)
        lock_resource_on_submit = step.options.get('lock_resource_on_job_submit', False)
        unlock_workflow_on_submit = step.options.get('unlock_workflow_on_job_submit', False)
        unlock_resource_on_submit = step.options.get('unlock_resource_on_job_submit', False)

        if lock_workflow_on_submit and unlock_workflow_on_submit:
            raise RuntimeError('Improperly configured SpatialCondorJobRWS: lock_workflow_on_job_submit and '
                               'unlock_workflow_on_job_submit options are mutually exclusive.')

        if lock_resource_on_submit and unlock_resource_on_submit:
            raise RuntimeError('Improperly configured SpatialCondorJobRWS: lock_resource_on_job_submit and '
                               'unlock_resource_on_job_submit options are mutually exclusive.')

        if lock_resource_on_submit:
            self.acquire_lock_and_log(request, session, resource)

        if lock_workflow_on_submit:
            self.acquire_lock_and_log(request, session, step.workflow)

        if unlock_resource_on_submit:
            self.release_lock_and_log(request, session, resource)

        if unlock_workflow_on_submit:
            self.release_lock_and_log(request, session, step.workflow)

    @staticmethod
    def get_working_directory(request, app):
        """
        Derive the working directory for the workflow.

        Args:
             request(HttpRequest): Django request instance.
             app(TethysAppBase): App class or instance.

        Returns:
            str: Path to working directory for the workflow.
        """
        user_workspace = app.get_user_workspace(request.user)
        working_directory = user_workspace.path
        return working_directory

    @staticmethod
    def serialize_parameters(step):
        """
        Serialize parameters from previous steps into a file for sending with the workflow.

        Args:
            step(ResourceWorkflowStep): The current step.

        Returns:
            str: path to the file containing serialized parameters.
        """
        parameters = {}
        previous_steps = step.workflow.get_previous_steps(step)

        for previous_step in previous_steps:
            parameters.update({previous_step.name: previous_step.to_dict()})

        return json.dumps(parameters)

    def process_lock_options_on_init(self, request, session, resource, step):
        """
        Process lock options when the view initializes.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            step(ResourceWorkflowStep): the step.
        """
        user_has_active_role = self.user_has_active_role(request, step)

        # Process lock options - only active users or permitted users can acquire user locks
        if user_has_active_role:
            # Bypass locking when view loads if lock on submit is requested
            if not step.options.get('lock_resource_on_job_submit') \
                    and not step.options.get('lock_workflow_on_job_submit'):
                super().process_lock_options_on_init(request, session, resource, step)

    def process_lock_options_after_submission(self, request, session, resource, step):
        """
        Process lock options after the step has been submitted and processed.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            step(ResourceWorkflowStep): the step.
        """
        if not step.options.get('unlock_resource_on_job_complete') \
                and not step.options.get('unlock_workflow_on_job_complete'):
            super().process_lock_options_after_submission(request, session, resource, step)
