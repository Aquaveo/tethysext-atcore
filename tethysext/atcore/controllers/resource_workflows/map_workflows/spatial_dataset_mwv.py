"""
********************************************************************************
* Name: spatial_dataset_mwv.py
* Author: nswain
* Created On: March 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
from django.shortcuts import render
from django.http import JsonResponse
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_data_mwv import SpatialDataMWV
from tethysext.atcore.models.resource_workflow_steps import SpatialDatasetRWS
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_controller
from tethysext.atcore.utilities import strip_list


class SpatialDatasetMWV(SpatialDataMWV):
    """
    Controller for a map workflow view requiring spatial input (drawing).
    """
    template_name = 'atcore/resource_workflows/spatial_dataset_mwv.html'
    valid_step_classes = [SpatialDatasetRWS]

    @workflow_step_controller(is_rest_controller=True)
    def get_popup_form(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
        """
        Handle GET requests with method get-attributes-form.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            workflow(ResourceWorkflow): the workflow.
            step(ResourceWorkflowStep): the step.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        # GET Parameters
        p_datasets = step.get_parameter('datasets')
        feature_id = request.GET.get('feature-id', None)

        # Get previously saved dataset, if there is one
        dataset = p_datasets.get(feature_id, None) if p_datasets else None
        max_rows = step.options.get('max_rows', step.DEFAULT_MAX_ROWS)

        # If not previously saved dataset, get the template dataset
        if dataset is None:
            dataset = step.options.get('template_dataset', step.DEFAULT_DATASET)

        # If the template dataset is empty (no rows),
        # generate rows to match the smaller of the initial row count and the max rows
        if dataset.empty:
            empty_rows = step.options.get('empty_rows', step.DEFAULT_EMPTY_ROWS)
            initial_rows = max_rows if empty_rows > max_rows else empty_rows
            dataset = pd.DataFrame(columns=dataset.columns, index=range(initial_rows), dtype=np.float64)

        # Reformat the data for rendering in the template
        rows = dataset.to_dict(orient='records')

        # Prepare columns dictionary
        column_is_numeric = {}
        for column in dataset.columns:
            is_numeric = is_numeric_dtype(dataset[column])
            column_is_numeric.update({column: is_numeric})

        context = {
            'feature_id': feature_id,
            'dataset_title': step.options.get('dataset_title', 'Dataset'),
            'columns': dataset.columns,
            'column_is_numeric': column_is_numeric,
            'rows': rows,
            'read_only_columns': step.options.get('read_only_columns', []),
            'plot_columns': step.options.get('plot_columns', []),
            'max_rows': max_rows,
        }

        return render(request, 'atcore/resource_workflows/components/spatial_dataset_form.html', context)

    @workflow_step_controller(is_rest_controller=True)
    def save_spatial_data(self, request, session, resource, workflow, step, back_url, *args, **kwargs):
        """
        Handle GET requests with method get-attributes-form.
        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.Session): Session bound to the resource, workflow, and step instances.
            resource(Resource): the resource this workflow applies to.
            workflow(ResourceWorkflow): the workflow.
            step(ResourceWorkflowStep): the step.
            args, kwargs: Additional arguments passed to the controller.

        Returns:
            HttpResponse: A Django response.
        """
        # Post process the dataset
        data = {}
        columns = step.options.get('template_dataset').columns

        for column in columns:
            c = request.POST.getlist(column, [])
            strip_list(c)
            data.update({column: c})

        # Save dataset as new pandas DataFrame
        dataset = pd.DataFrame(data=data, columns=columns, dtype=np.float64)

        # Save the data to the datasets parameter of the step
        p_datasets = step.get_parameter('datasets')

        # Lazy load the dataset parameter as a dictionary
        if p_datasets is None or not isinstance(p_datasets, dict):
            p_datasets = {}

        # Index datasets by feature id
        feature_id = request.POST.get('feature-id', None)
        p_datasets[feature_id] = dataset

        # Reset the parameter to None for changes to be detected and saved.
        step.set_parameter('datasets', None)
        session.commit()

        # Save the new value of the datasets
        step.set_parameter('datasets', p_datasets)
        session.commit()

        return JsonResponse({'success': True})

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

            # Update the status of the step
            step.set_status(step.ROOT_STATUS_KEY, step.STATUS_COMPLETE)
            step.set_attribute(step.ATTR_STATUS_MESSAGE, None)
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
