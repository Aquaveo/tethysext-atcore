"""
********************************************************************************
* Name: resource_workflows.py
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import inspect
from django.utils.text import slugify
from tethysext.atcore.controllers.resource_workflows import ResourceWorkflowView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource, ResourceWorkflow


def urls(url_map_maker, app, persistent_store_name, workflow_pairs, base_url_path='', custom_models=()):
    """
    Generate UrlMap objects for each workflow model-controller pair provided. To link to pages provided by the app_users extension use the name of the url with your app namespace:

    ::

        {% url 'my_first_app:a_workflow_workflow', resource_id=resource.id, workflow_id=workflow.id %}

        OR

        reverse('my_first_app:a_workflow_workflow_step', kwargs={'resource_id': resource.id, 'workflow_id': workflow.id, 'step_id': step.id})

    Args:
        url_map_maker(UrlMap): UrlMap class bound to app root url.
        app(TethysAppBase): instance of Tethys app class.
        persistent_store_name(str): name of persistent store database setting the controllers should use to create sessions.
        workflow_pairs(2-tuple<ResourceWorkflow, ResourceWorkflowView>): Pairs of ResourceWorkflow models and ResourceWorkFlow views.
        base_url_path(str): url path to prepend to all app_user urls (e.g.: 'foo/bar').
        custom_models(cls): custom subclasses of AppUser, Organization, or Resource models.

    Url Map Names:
        <workflow_type>_workflow <resource_id> <workflow_id>
        <workflow_type>_workflow_step <resource_id> <workflow_id> <step_id>

    Returns:
        tuple: UrlMap objects for the app_users extension.
    """  # noqa: F401, E501
    # Validate kwargs
    if base_url_path:
        if base_url_path.startswith('/'):
            base_url_path = base_url_path[1:]
        if base_url_path.endswith('/'):
            base_url_path = base_url_path[:-1]

    # Default model classes
    _AppUser = AppUser
    _Organization = Organization
    _Resource = Resource

    for custom_model in custom_models:
        if inspect.isclass(custom_model) and issubclass(custom_model, AppUser):
            _AppUser = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Organization):
            _Organization = custom_model
        elif inspect.isclass(custom_model) and issubclass(custom_model, Resource):
            _Resource = custom_model
        else:
            raise ValueError('custom_models must contain only subclasses of AppUser, Resources, or Organization.')

    # Url Patterns
    workflow_url = slugify(_Resource.DISPLAY_TYPE_PLURAL.lower()) + '/{resource_id}/workflows/{workflow_id}'  # noqa: E222, E501
    workflow_step_url = slugify(_Resource.DISPLAY_TYPE_PLURAL.lower()) + '/{resource_id}/workflows/{workflow_id}/step/{step_id}'  # noqa: E222, E501

    url_maps = []

    for _ResourceWorkflow, _ResourceWorkflowView in workflow_pairs:
        if not _ResourceWorkflow or not inspect.isclass(_ResourceWorkflow) \
           or not issubclass(_ResourceWorkflow, ResourceWorkflow):
            raise ValueError('Must provide a valid ResourceWorkflow model as the first item in the '
                             'workflow_pairs argument.')

        if not _ResourceWorkflowView or not inspect.isclass(_ResourceWorkflowView) \
           or not issubclass(_ResourceWorkflowView, ResourceWorkflowView):
            raise ValueError('Must provide a valid ResourceWorkflowView controller as the second item in the '
                             'workflow_pairs argument.')

        workflow_name = '{}_workflow'.format(_ResourceWorkflow.TYPE)
        workflow_step_name = '{}_workflow_step'.format(_ResourceWorkflow.TYPE)

        url_maps.extend([
            url_map_maker(
                name=workflow_name,
                url='/'.join([base_url_path, workflow_url]) if base_url_path else workflow_url,
                controller=_ResourceWorkflowView.as_controller(
                    _app=app,
                    _persistent_store_name=persistent_store_name,
                    _AppUser=_AppUser,
                    _Organization=_Organization,
                    _Resource=_Resource,
                    _ResourceWorkflow=_ResourceWorkflow,
                )
            ),
            url_map_maker(
                name=workflow_step_name,
                url='/'.join([base_url_path, workflow_step_url]) if base_url_path else workflow_step_url,
                controller=_ResourceWorkflowView.as_controller(
                    _app=app,
                    _persistent_store_name=persistent_store_name,
                    _AppUser=_AppUser,
                    _Organization=_Organization,
                    _Resource=_Resource,
                    _ResourceWorkflow=_ResourceWorkflow,
                )
            )
        ])

    return url_maps