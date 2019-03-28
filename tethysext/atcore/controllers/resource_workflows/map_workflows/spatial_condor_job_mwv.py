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
from tethys_sdk.gizmos import MVLayer, MapView
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS, SpatialInputRWS, \
    SpatialDatasetRWS, SpatialAttributesRWS
from tethysext.atcore.services.condor_workflow_manager import ResourceWorkflowCondorJobManager


log = logging.getLogger(__name__)


class SpatialCondorJobMWV(MapWorkflowView):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_condor_job_mwv.html'
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

        for step in previous_steps:
            if isinstance(step, SpatialInputRWS):
                geometry = step.get_parameter('geometry')
                if not geometry:
                    log.warning('Parameter "geometry" for {} with name "{}" was '
                                'not defined.'.format(type(step), step.name))
                    continue

                # Build the Layer
                workflow_layer = self._build_mv_layer(step, geometry)

                # Save for building layer group later
                workflow_layers.append(workflow_layer)

                # Add layer to beginning the map's of layer list
                map_view.layers.insert(0, workflow_layer)

            elif isinstance(step, SpatialAttributesRWS):
                # TODO: Figure out out to map datasets attributes to the layers...
                # TODO: Implement support for complex data types like the Hydrographs
                pass

            elif isinstance(step, SpatialDatasetRWS):
                # TODO: Figure out out to map datasets attributes to the layers...
                # TODO: Implement support for complex data types like the Hydrographs
                pass

        # Build the Layer Group for Workflow Layers
        workflow_layer_group = {
            'id': 'workflow_datasets',
            'display_name': 'Workflow Datasets',
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
            layer_options={'visible': True},
            feature_selection=True
        )
        return workflow_layer

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

            # Submit job
            condor_job_manager.run_job()

            # Update status of the resource workflow step
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_WORKING)
            step.set_attribute(step.ATTR_STATUS_MESSAGE, None)
            session.commit()

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

    def create_layer_from_geometry(self, geometry):
        """

        :param geometry:
        :return:
        """
