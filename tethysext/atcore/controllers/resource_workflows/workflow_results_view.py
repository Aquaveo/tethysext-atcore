from tethys_apps.utilities import get_active_app
from tethysext.atcore.models.app_users import ResourceWorkflowResult
from tethysext.atcore.models.resource_workflow_steps import ResultsResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowView
from tethysext.atcore.controllers.resource_workflows.mixins import ResultViewMixin


class WorkflowResultsView(ResourceWorkflowView, ResultViewMixin):
    """
    Base class for result views.
    """
    template_name = 'atcore/resource_workflows/workflow_results_view.html'
    valid_step_classes = [ResultsResourceWorkflowStep]
    valid_result_classes = [ResourceWorkflowResult]

    def get_context(self, request, session, resource, context, model_db, workflow_id, step_id, result_id, *args,
                    **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            workflow_id (str): UUID of the workflow.
            step_id (str): UUID of the step.
            result_id (str): UUID of the result.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        # Results steps are marked as complete when viewed
        step = self.get_step(request, step_id, session)
        step.set_status(step.ROOT_STATUS_KEY, step.STATUS_COMPLETE)
        session.commit()

        # Call super class get_context first
        context = super().get_context(
            request=request,
            session=session,
            resource=resource,
            context=context,
            model_db=model_db,
            workflow_id=workflow_id,
            step_id=step_id,
            *args, **kwargs
        )

        # Validate the result
        result = self.get_result(request=request, result_id=result_id, session=session)
        self.validate_result(request=request, session=session, result=result)

        # Get current step
        current_step = context['current_step']

        # Save the current result view
        current_step.set_last_result(result)

        # Build the results cards
        results = self.build_result_cards(current_step)

        # Get the url map name for results
        result_url_name = self.get_result_url_name(request, current_step.workflow)

        context.update({
            'results': results,
            'result_url_name': result_url_name,
        })

        if getattr(result, 'layers', None) and result.layers:
            context['layers'] = result.layers

        return context

    @staticmethod
    def get_result_url_name(request, workflow):
        """
        Derive url map name for the given result view.
        Args:
            request(HttpRequest): The request.
            workflow(ResourceWorkflow): The current workflow.

        Returns:
            str: name of the url pattern for the given workflow step views.
        """
        active_app = get_active_app(request)
        url_map_name = '{}:{}_workflow_step_result'.format(active_app.url_namespace, workflow.type)
        return url_map_name

    def build_result_cards(self, step):
        """
        Build cards used by template to render the list of steps for the workflow.
        Args:
            step(ResourceWorkflowStep): the step to which the results belong.

        Returns:
            list<dict>: one dictionary for each result in the step.
        """
        results = []
        for result in step.results:
            result_dict = {
                'id': str(result.id),
                'name': result.name,
                'description': result.description,
                'type': result.type,
            }
            results.append(result_dict)

        return results

    def validate_result(self, request, session, result):
        """
        Validate the result being used for this view. Raises TypeError if result is invalid.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            result(ResourceWorkflowResult): The result to be rendered.

        Raises:
            TypeError: if step is invalid.
        """
        # Initialize drawing tools for spatial input parameter types.
        if not any([isinstance(result, valid_class) for valid_class in self.valid_result_classes]):
            raise TypeError('Invalid result type for view: "{}". Must be one of "{}".'.format(
                type(result).__name__,
                '", "'.join([valid_class.__name__ for valid_class in self.valid_result_classes])
            ))

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
        # Always set the status to COMPLETE
        step.set_status(step.ROOT_STATUS_KEY, step.STATUS_COMPLETE)
        session.commit()

        return super().process_step_data(
            request=request,
            session=session,
            step=step,
            model_db=model_db,
            current_url=current_url,
            previous_url=previous_url,
            next_url=next_url
        )

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
        pass
