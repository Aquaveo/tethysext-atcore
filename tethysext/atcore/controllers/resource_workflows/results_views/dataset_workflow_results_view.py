"""
********************************************************************************
* Name: dataset_workflow_result_view.py
* Author: nswain
* Created On: June 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from collections import OrderedDict
from tethys_sdk.gizmos import DataTableView
from tethysext.atcore.models.resource_workflow_results import DatasetWorkflowResult
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView
from tethys_sdk.permissions import has_permission


log = logging.getLogger(f'tethys.{__name__}')


class DatasetWorkflowResultView(WorkflowResultsView):
    """
    Dataset Result View Controller
    """
    template_name = 'atcore/resource_workflows/dataset_workflow_results_view.html'
    valid_result_classes = [DatasetWorkflowResult]

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
            *args,
            request=request,
            session=session,
            resource=resource,
            context=context,
            workflow_id=workflow_id,
            step_id=step_id,
            result_id=result_id,
            **kwargs
        )

        # Get the result
        result = self.get_result(request=request, result_id=result_id, session=session)

        # Get datasets
        datasets = result.datasets

        # Get options
        options = result.options

        # Page title same as result name
        page_title = options.get('page_title', result.name)

        # Get can_export_datatable permission
        can_export_datatable = has_permission(request, 'can_export_datatable')

        for ds in datasets:
            # Check if the export options is there
            dom_attribute = ""
            if 'show_export_button' in ds.keys():
                if ds['show_export_button'] and can_export_datatable:
                    # B stands for button.
                    dom_attribute = "Bfrtip"

            data_table = DataTableView(
                column_names=ds['dataset'].columns,
                rows=[list(record.values()) for record in ds['dataset'].to_dict(orient='records', into=OrderedDict)],
                dom=dom_attribute,
                **options.get('data_table_kwargs', {})
            )
            ds.update({'data_table': data_table})

        base_context.update({
            'no_dataset_message': options.get('no_dataset_message', 'No dataset found.'),
            'page_title': page_title,
            'datasets': datasets
        })

        return base_context
