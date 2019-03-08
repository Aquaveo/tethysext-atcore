"""
********************************************************************************
* Name: spatial_input_mwv.py
* Author: nswain
* Created On: January 21, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from tethysext.atcore.controllers.resource_workflows.map_workflows import MapWorkflowView
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS
from tethysext.atcore.services.condor_workflow_manager import CondorWorkflowJobManager


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
        # TODO: RENDER DATA ON MAP FOR REVIEW

        # SHOW SPATIAL DATASETS/ATTRIBUTES as READONLY POPUPS
        # SHOW SPATIAL INPUT FEATURES
        # EACH STEP ON IT'S OWN LAYER

        # # Get Map View
        # map_view = context['map_view']
        #
        # # Turn off feature selection
        # self.set_feature_selection(map_view=map_view, enabled=False)
        #
        # # Add layer for current geometry
        # enabled_controls = ['Modify', 'Delete', 'Move', 'Pan']
        # if current_step.options['allow_drawing']:
        #     for elem in current_step.options['shapes']:
        #         if elem == 'points':
        #             enabled_controls.append('Point')
        #         elif elem == 'lines':
        #             enabled_controls.append('LineString')
        #         elif elem == 'polygons':
        #             enabled_controls.append('Polygon')
        #         elif elem == 'extents':
        #             enabled_controls.append('Box')
        #         else:
        #             raise ValueError('Invalid shapes defined: {}.'.format(elem))
        #
        # # Load the currently saved geometry, if any.
        # current_geometry = current_step.get_parameter('geometry')
        #
        # # Configure drawing
        # draw_options = MVDraw(
        #     controls=enabled_controls,
        #     initial='Pan',
        #     initial_features=current_geometry,
        #     output_format='GeoJSON',
        #     snapping_enabled=current_step.options['snapping_enabled'],
        #     snapping_layer=current_step.options['snapping_layer'],
        #     snapping_options=current_step.options['snapping_options']
        # )
        #
        # if draw_options is not None and 'map_view' in context:
        #     map_view.draw = draw_options
        #
        # # Save changes to map view
        # context.update({'map_view': map_view})

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
            :param model_db: 
        """  # noqa: E501
        # Validate data if going to next step
        if 'next-submit' in request.POST:
            step.validate()

            # Get options
            scheduler_name = step.options.get('scheduler', None)
            if not scheduler_name:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "scheduler" option supplied.')

            job_dicts = step.options.get('jobs', None)
            if not job_dicts:
                raise RuntimeError('Improperly configured SpatialCondorJobRWS: no "jobs" option supplied.')

            # Create the CondorWorkflowJobNodes
            jobs = self.build_job_nodes(job_dicts)

            # Define the working directory
            app = self.get_app()
            working_directory = self.get_working_directory(request, app)

            # Serialize parameters from all previous steps into a parameters.json file to send to the job
            params_file = self.serialize_parameters(step)

            # Setup the Condor Workflow
            condor_job_manager = CondorWorkflowJobManager(
                session=session,
                model_db=model_db,
                resource_workflow_step=step,
                jobs=jobs,
                user=request.user,
                working_directory=working_directory,
                app=app,
                scheduler_name=scheduler_name,
                input_files=[params_file],
            )

            # TODO: Uncomment to submit job
            # condor_job_manager.run_job()

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
    def build_job_nodes(job_dicts):
        """
        Build CondorWorkflowJobNodes from the job_dicts provided.

        Args:
            job_dicts(list<dicts>): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.

        Returns:
            list<CondorWorkflowJobNodes>: the job nodes.
        """
        from tethys_sdk.jobs import CondorWorkflowJobNode

        jobs = []

        for job_dict in job_dicts:
            # Pop-off keys to be handled separately
            attributes = job_dict.pop('attributes', {})

            job = CondorWorkflowJobNode(*job_dict)

            for attribute, value in attributes.items():
                job.set_attribute(attribute, value)

            jobs.append(job)

        return jobs

    def serialize_parameters(self, step):
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
            parameters.update({previous_step.name: previous_step.get_parameters()})
        import pdb; pdb.set_trace()
        return parameters
