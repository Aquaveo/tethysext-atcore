"""
********************************************************************************
* Name: plot_workflow_result_view.py
* Author: nathan, htran, msouff
* Created On: Oct 7, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
from tethysext.atcore.models.resource_workflow_results import PlotWorkflowResult
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethys_sdk.gizmos import BokehView
from tethys_sdk.gizmos import PlotlyView

log = logging.getLogger(f'tethys.{__name__}')


class PlotWorkflowResultView(WorkflowResultsView):
    """
    Plot Result View Controller
    """
    template_name = 'atcore/resource_workflows/plot_workflow_results_view.html'
    valid_result_classes = [PlotWorkflowResult]

    def get_context(self, request, session, resource, context, workflow_id, step_id, result_id, *args,
                    **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            workflow_id (str): The id of the workflow.
            step_id (str): The id of the step.
            result_id (str): The id of the result.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        base_context = super().get_context(
            request=request,
            session=session,
            resource=resource,
            context=context,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id,
            *args, **kwargs
        )

        # Get the result
        result = self.get_result(request=request, result_id=result_id, session=session)

        # Get options.
        options = result.options

        # Get plot view gizmo
        renderer = options.get('renderer', 'plotly')
        plot_view_params = dict(plot_input=result.get_plot_object(), height='95%', width='95%')
        plot_view = BokehView(**plot_view_params) if renderer == 'bokeh' else PlotlyView(**plot_view_params)

        # Page title same as result name.
        page_title = options.get('page_title', result.name)

        base_context.update({
            'page_title': page_title,
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'plot_view_input': plot_view,
        })

        return base_context
