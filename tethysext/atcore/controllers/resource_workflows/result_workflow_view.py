from tethys_apps.utilities import get_active_app
from tethysext.atcore.models.resource_workflow_steps import ResultsResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowView


class ResultWorkflowView(ResourceWorkflowView):
    """
    Base class for result views.
    """
    template_name = ''
    valid_step_classes = [ResultsResourceWorkflowStep]

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

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
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

        # Get current step
        current_step = context['current_step']

        # Build the results cards
        results = self.build_result_cards(current_step)

        # Get the url map name for results
        result_url_name = self.get_result_url_name(request, current_step.workflow)

        context.update({
            'results': results,
            'result_url_name': result_url_name,
        })

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
        url_map_name = '{}:{}_workflow_step_result'.format(active_app.namespace, workflow.type)
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
                'id': result.id,
                'name': result.id,
                'description': result.description,
                'type': result.type,
            }
            results.append(result_dict)

        return results
