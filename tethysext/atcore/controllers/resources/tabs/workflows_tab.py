"""
********************************************************************************
* Name: workflows_tab.py
* Author: nswain
* Created On: November 13, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging
from abc import abstractmethod

from django.http import JsonResponse
from django.shortcuts import reverse, redirect
from django.contrib import messages
from tethys_sdk.permissions import has_permission

from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.controllers.utilities import get_style_for_status
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.controllers.resources.tabs.resource_tab import ResourceTab


log = logging.getLogger('tethys.' + __name__)


class ResourceWorkflowsTab(ResourceTab):
    """
    A tab for the TabbedResourceDetails view that lists any ResourceWorkflows associated with the Resource. Users can add and delete ResourceWorkflows and launch them from this view as well.

    Required URL Variables:
        resource_id (str): the ID of the Resource.
        tab_slug (str): Portion of URL that denotes which tab is active.

    Properties:
        show_all_workflows (bool): List all workflows, not just those created by the current user. Defaults to True.
        show_all_workflows_roles list<Roles>: List of user Roles that are allowed to see all workflows when show_all_workflows is False. Defaults to: [Roles.APP_ADMIN, Roles.DEVELOPER, Roles.ORG_ADMIN, Roles.ORG_REVIEWER].

    Class Methods:
        get_workflow_types (required): Return a dictionary mapping of ResourceWorkflow.TYPE to ResourceWorkflow classes (e.g. {MyResourceWorkflow.TYPE: MyResourceWorkflow} ). The list of available workflows in the New Workflow dialog is derived from this object.

    Methods:
        get_map_manager (optional): Return your app-specific MapManager. Required if your workflows use spatial steps.
        get_spatial_manager (optional): Return your app-specific SpatialManager. Required if your workflows use spatial steps.
        get_sds_setting_name (optional): Return the name of the SpatialDatasetService setting. Required if your workflows use spatial steps.
    """  # noqa: E501
    template_name = 'atcore/resources/tabs/workflows.html'
    http_method_names = ['get', 'post', 'delete']
    js_requirements = ResourceTab.js_requirements + [
        'atcore/js/enable-tooltips.js',
        'atcore/js/delete_row.js',
        'atcore/resources/workflows_tab.js'
    ]
    css_requirements = ResourceTab.css_requirements + [
        'atcore/css/btn-fab.css',
        'atcore/css/flat-modal.css',
        'atcore/resource_workflows/workflows.css'
    ]
    modal_templates = [
        'atcore/resources/tabs/new_workflow_modal.html',
        'atcore/resources/tabs/delete_workflow_modal.html'
    ]
    post_load_callback = 'workflows_tab_loaded'
    show_all_workflows = True
    show_all_workflows_roles = [Roles.APP_ADMIN, Roles.DEVELOPER, Roles.ORG_ADMIN, Roles.ORG_REVIEWER]

    @classmethod
    @abstractmethod
    def get_workflow_types(cls):
        """
        A hook that must be used to define a the ResourceWorkflows supported by this tab view. The list of available workflows in the New Workflow dialog is derived from this object.

        Returns:
            dict: mapping of ResourceWorkflow.TYPE to ResourceWorkflow classes (e.g. {MyResourceWorkflow.TYPE: MyResourceWorkflow} ).
        """  # noqa: E501
        return {}

    def get_map_manager(self):
        """
        A hook that can be used to define your app-specific MapManager. Required if your workflows use spatial steps.

        Returns:
            MapManagerBase: an app-specific MapMangerBase class.
        """  # noqa: E501
        return MapManagerBase

    def get_spatial_manager(self):
        """
        A hook that can be used to define your app-specific SpatialManager. Required if your workflows use spatial steps.

        Returns:
            BaseSpatialManager: an app-specific BaseSpatialManager class.
        """  # noqa: E501
        return BaseSpatialManager

    def get_sds_setting_name(self):
        """
        Return the name of the SpatialDatasetService setting. Required if your workflows use spatial steps.

        Returns:
            str: the name of the SpatialDatasetService setting for your app.
        """  # noqa: E501
        return None

    @classmethod
    def get_tabbed_view_context(cls, request, context):
        """
        Add context specific to the ResourceWorkflowsTab to the TabbedResourceDetails view.
        """
        return {'workflow_types': cls.get_workflow_types()}

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for the ResourceWorkflowsTab template that is used to generate the tab content.
        """
        _AppUser = self.get_app_user_model()
        app_user = _AppUser.get_app_user_from_request(request, session)
        app_user_role = app_user.role
        if self.show_all_workflows or app_user_role in self.show_all_workflows_roles:
            workflows = session.query(ResourceWorkflow). \
                filter(ResourceWorkflow.resource_id == resource.id). \
                order_by(ResourceWorkflow.date_created.desc()). \
                all()
        else:
            workflows = session.query(ResourceWorkflow). \
                filter(ResourceWorkflow.resource_id == resource.id). \
                filter(ResourceWorkflow.creator_id == app_user.id). \
                order_by(ResourceWorkflow.date_created.desc()). \
                all()

        # Build up workflow cards for workflows table
        workflow_cards = []

        for workflow in workflows:
            status = workflow.get_status()
            app_namespace = self.get_app().url_namespace
            url_name = f'{app_namespace}:{workflow.TYPE}_workflow'
            href = reverse(url_name, args=(resource.id, str(workflow.id)))
            status_style = get_style_for_status(status)

            if status == workflow.STATUS_PENDING or status == '' or status is None:
                statusdict = {
                    'title': 'Begin',
                    'style': 'primary',
                    'href': href
                }

            elif status == workflow.STATUS_WORKING:
                statusdict = {
                    'title': 'Running',
                    'style': status_style,
                    'href': href
                }

            elif status == workflow.STATUS_COMPLETE:
                statusdict = {
                    'title': 'View Results',
                    'style': status_style,
                    'href': href
                }

            elif status == workflow.STATUS_ERROR:
                statusdict = {
                    'title': 'Continue',
                    'style': 'primary',
                    'href': href
                }

            elif status == workflow.STATUS_FAILED:
                statusdict = {
                    'title': 'Failed',
                    'style': status_style,
                    'href': href  # TODO: MAKE IT POSSIBLE TO RESTART WORKFLOW?
                }

            else:
                statusdict = {
                    'title': status,
                    'style': status_style,
                    'href': href
                }

            is_creator = request.user.username == workflow.creator.username if workflow.creator else True

            workflow_cards.append({
                'id': str(workflow.id),
                'name': workflow.name,
                'type': workflow.DISPLAY_TYPE_SINGULAR,
                'creator': workflow.creator.username if workflow.creator else 'Unknown',
                'date_created': workflow.date_created,
                'resource': workflow.resource,
                'status': statusdict,
                'can_delete': has_permission(request, 'delete_any_workflow') or is_creator
            })

        context.update({'workflow_cards': workflow_cards})
        return context

    def post(self, request, resource_id, *args, **kwargs):
        """
        Handle the New Workflow form submissions for this tab.
        """
        params = request.POST
        all_workflow_types = self.get_workflow_types()

        if 'new-workflow' in params:
            # Params
            workflow_name = params.get('workflow-name', '')
            workflow_type = params.get('workflow-type', '')

            if not workflow_name:
                messages.error(request, 'Unable to create new workflow: no name given.')
                return redirect(request.path)

            if not workflow_type or workflow_type not in all_workflow_types:
                messages.error(request, 'Unable to create new workflow: invalid workflow type.')
                return redirect(request.path)

            # Create new workflow
            _AppUser = self.get_app_user_model()
            make_session = self.get_sessionmaker()
            session = make_session()
            request_app_user = _AppUser.get_app_user_from_request(request, session)

            try:
                WorkflowModel = all_workflow_types[workflow_type]
                workflow = WorkflowModel.new(
                    app=self._app,
                    name=workflow_name,
                    resource_id=resource_id,
                    creator_id=request_app_user.id,
                    geoserver_name=self.get_sds_setting_name(),
                    map_manager=self.get_map_manager(),
                    spatial_manager=self.get_spatial_manager(),
                )
                session.add(workflow)
                session.commit()

            except Exception:
                message = 'An unexpected error occurred while creating the new workflow.'
                log.exception(message)
                messages.error(request, message)
                return redirect(request.path)
            finally:
                session.close()

            messages.success(
                request,
                f'Successfully created new {all_workflow_types[workflow_type].DISPLAY_TYPE_SINGULAR}: {workflow_name}'
            )

            return redirect(request.path)

        # Redirect/render the normal GET page by default with warning message.
        messages.warning(request, 'Unable to perform requested action.')
        return redirect(request.path)

    def delete(self, request, resource_id, *args, **kwargs):
        """
        Handle DELETE requests for this tab.
        """
        session = None
        try:
            workflow_id = request.GET.get('id', '')
            log.debug(f'Workflow ID: {workflow_id}')

            make_session = self.get_sessionmaker()
            session = make_session()

            # Get the workflow
            workflow = session.query(ResourceWorkflow).get(workflow_id)

            # Delete the workflow
            session.delete(workflow)
            session.commit()
            log.info(f'Deleted Workflow: {workflow}')
        except:  # noqa: E722
            log.exception('An error occurred while attempting to delete a workflow.')
            return JsonResponse({'success': False, 'error': 'An unexpected error has occurred.'})
        finally:
            session and session.close()

        return JsonResponse({'success': True})
