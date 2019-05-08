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
from django.shortcuts import render
from tethys_sdk.gizmos import MVLayer, JobsTable
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS, SpatialInputRWS, \
    SpatialResourceWorkflowStep
from tethysext.atcore.services.condor_workflow_manager import ResourceWorkflowCondorJobManager


log = logging.getLogger(__name__)


class SpatialCondorJobMWV(MapWorkflowView):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_condor_job_mwv.html'
    next_title = 'Run Process'
    valid_step_classes = [SpatialCondorJobRWS]

    def process_step_options(self, request, session, context, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
        # Get Map View and Layer Groups
        map_view = context['map_view']
        layer_groups = context['layer_groups']

        # Turn off feature selection on current layers
        self.set_feature_selection(map_view=map_view, enabled=False)

        # Process each previous step
        previous_steps = current_step.workflow.get_previous_steps(current_step)

        workflow_layers = []
        steps_to_skip = set()
        mappable_step_types = (SpatialInputRWS,)

        for step in previous_steps:
            # Skip these steps
            if step in steps_to_skip or not isinstance(step, mappable_step_types):
                continue

            # If step has a child, get geojson from the child,
            # which will include the properties added by the child
            if step.child is not None:
                # Child step must be a SpatialResourceWorkflowStep
                if not isinstance(step.child, SpatialResourceWorkflowStep):
                    continue

                # Child geojson should include properties it adds to the features
                geometry = step.child.to_geojson()

                # Skip child step in the future to avoid adding it twice
                steps_to_skip.add(step.child)

            # Otherwise, get the geojson from this step directly
            else:
                # Child step must be a SpatialResourceWorkflowStep
                if not isinstance(step, SpatialResourceWorkflowStep):
                    continue

                geometry = step.to_geojson()

            if not geometry:
                log.warning('Parameter "geometry" for {} was not defined.'.format(step))
                continue

            # Build the Layer
            workflow_layer = self._build_mv_layer(step, geometry)

            # Save for building layer group later
            workflow_layers.append(workflow_layer)

            # Add layer to beginning the map's of layer list
            map_view.layers.insert(0, workflow_layer)

        # Build the Layer Group for Workflow Layers
        workflow_layer_group = {
            'id': 'workflow_datasets',
            'display_name': '{} Datasets'.format(current_step.workflow.DISPLAY_TYPE_SINGULAR),
            'control': 'checkbox',
            'layers': workflow_layers,
            'visible': True
        }

        layer_groups.insert(0, workflow_layer_group)

        # Save changes to map view and layer groups
        context.update({
            'map_view': map_view,
            'layer_groups': layer_groups
        })

    @staticmethod
    def _build_mv_layer(step, geometry):
        """
        Build an MVLayer object given a step and a GeoJSON formatted geometry.

        Args:
            step(SpatialResourceWorkflowStep): The step the geometry is associated with.
            geometry(dict): GeoJSON Python equivalent.

        Returns:
            MVLayer: the layer object.
        """
        # Derive names from step options
        plural_name = step.options.get('plural_name')
        plural_codename = plural_name.lower().replace(' ', '_')
        singular_name = step.options.get('singular_name')
        layer_name = '{}_{}'.format(step.id, plural_codename)

        # Bind geometry features to layer via layer name
        for feature in geometry['features']:
            feature['properties']['layer_name'] = layer_name

        # Define default styles for layers
        color = 'gold'
        style_map = {
            'Point': {'ol.style.Style': {
                'image': {'ol.style.Circle': {
                    'radius': 5,
                    'fill': {'ol.style.Fill': {
                        'color': color,
                    }},
                    'stroke': {'ol.style.Stroke': {
                        'color': color,
                    }}
                }}
            }},
            'LineString': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': color,
                    'width': 2
                }}
            }},
            'Polygon': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': color,
                    'width': 2
                }},
                'fill': {'ol.style.Fill': {
                    'color': 'rgba(255, 215, 0, 0.1)'
                }}
            }},
        }

        # Define the workflow MVLayer
        workflow_layer = MVLayer(
            source='GeoJSON',
            options=geometry,
            legend_title=plural_name,
            data={
                'layer_name': layer_name,
                'layer_variable': '{}-{}'.format(step.TYPE, plural_codename),
                'popup_title': singular_name,
                'excluded_properties': ['id', 'type', 'layer_name'],
            },
            layer_options={
                'visible': True,
                'style_map': style_map
            },
            feature_selection=True
        )
        return workflow_layer

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
        step_status = current_step.get_status(current_step.ROOT_STATUS_KEY)
        if step_status == current_step.STATUS_WORKING:
            return self.render_condor_jobs_table(request, resource, workflow, current_step)

    def render_condor_jobs_table(self, request, resource, workflow, current_step):
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

        jobs_table = JobsTable(
            jobs=[step_job],
            column_fields=('description', 'creation_time', ),
            hover=True,
            striped=True,
            condensed=False,
            show_detailed_status=True,
            delete_btn=False,
        )

        # Build step cards
        steps = self.build_step_cards(workflow)

        # Get the current app
        step_url_name = self.get_step_url_name(request, workflow)

        context = {
            'resource': resource,
            'workflow': workflow,
            'steps': steps,
            'current_step': current_step,
            'step_url_name': step_url_name,
            'back_url': self.back_url,
            'nav_title': '{}: {}'.format(resource.name, workflow.name),
            'nav_subtitle': workflow.DISPLAY_TYPE_SINGULAR,
            'jobs_table': jobs_table
        }

        return render(request, 'atcore/resource_workflows/spatial_condor_jobs_table.html', context)

    def process_step_data(self, request, session, step, model_db, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            step(ResourceWorkflowStep): The step to be updated.
            model_db(ModelDatabase): The model database associated with the resource.
            current_url(str): URL to step.
            previous_url(str): URL to the previous step.
            next_url(str): URL to the next step.

        Returns:
            HttpResponse: A Django response.

        Raises:
            ValueError: exceptions that occur due to user error, provide helpful message to help user solve issue.
            RuntimeError: exceptions that require developer attention.
        """  # noqa: E501
        # Validate data if going to next step
        if 'next-submit' in request.POST:
            step.validate()

            # Get options
            scheduler_name = step.options.get('scheduler', None)
            if not scheduler_name:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "scheduler" option supplied.')

            jobs = step.options.get('jobs', None)
            if not jobs:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "jobs" option supplied.')

            # Define the working directory
            app = self.get_app()
            working_directory = self.get_working_directory(request, app)

            # Setup the Condor Workflow
            condor_job_manager = ResourceWorkflowCondorJobManager(
                session=session,
                model_db=model_db,
                resource_workflow_step=step,
                jobs=jobs,
                user=request.user,
                working_directory=working_directory,
                app=app,
                scheduler_name=scheduler_name,
            )

            # Serialize parameters from all previous steps into json
            serialized_params = self.serialize_parameters(step)

            # Write serialized params to file for transfer
            params_file_path = os.path.join(condor_job_manager.working_directory, 'workflow_params.json')
            with open(params_file_path, 'w') as params_file:
                params_file.write(serialized_params)

            # Add parameter file to workflow input files
            condor_job_manager.input_files.append(params_file_path)

            # Prepare the job
            job_id = condor_job_manager.prepare()

            # Submit job
            condor_job_manager.run_job()

            # Update status of the resource workflow step
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_WORKING)
            step.set_attribute(step.ATTR_STATUS_MESSAGE, None)

            # Save the job id to the step for later reference
            step.set_attribute('condor_job_id', job_id)

            # Allow the step to track statuses on each "sub-job"
            step.set_attribute('condor_job_statuses', [])
            session.commit()

            # Redirect back to self
            next_url = request.path

        return super().process_step_data(request=request, session=session, step=step, model_db=model_db,
                                         current_url=current_url, previous_url=previous_url, next_url=next_url)

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
