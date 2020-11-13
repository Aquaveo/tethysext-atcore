"""
********************************************************************************
* Name: workflows_tab.py
* Author: nswain
* Created On: November 13, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import logging

from django.http import JsonResponse
from django.shortcuts import reverse
from django.contrib import messages
from tethys_sdk.permissions import has_permission

from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.controllers.utilities import get_style_for_status
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.controllers.resources.tabs.resource_tab import ResourceTab


log = logging.getLogger('tethys.' + __name__)


class ResourceWorkflowsTab(ResourceTab):
    """
    Description.

    Properties:
        template_name:
        base_template:
        css_requirements:
        js_requirements:
        modal_templates:
        post_load_callback:
        show_all_workflows:
        show_all_workflows_roles:
        resource_workflows:
    """
    template_name = 'atcore/resources/tabs/workflows.html'
    js_requirements = ResourceTab.js_requirements + [
        'atcore/js/enable-tooltips.js'
    ]
    css_requirements = ResourceTab.css_requirements + [
        'atcore/css/btn-fab.css',
        'atcore/css/flat-modal.css',
        'atcore/resource_workflows/workflows.css'
    ]
    post_load_callback = 'enable_tooltips'
    modal_templates = [
        'atcore/resources/tabs/new_workflow_modal.html',
        'atcore/resources/tabs/delete_workflow_modal.html'
    ]
    show_all_workflows = True
    show_all_workflows_roles = [Roles.APP_ADMIN, Roles.DEVELOPER, Roles.ORG_ADMIN, Roles.ORG_REVIEWER]
    resource_workflows = None

    def get_context(self, request, session, resource, context, *args, **kwargs):
        """
        Build context for Summary Tab template.
        """
        make_session = self.get_sessionmaker()
        session = make_session()
        _AppUser = self.get_app_user_model()

        try:
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
                app_namespace = self.get_app().namespace
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
                    'type': self.resource_workflows[workflow.type].DISPLAY_TYPE_SINGULAR,
                    'creator': workflow.creator.username if workflow.creator else 'Unknown',
                    'date_created': workflow.date_created,
                    'resource': workflow.resource,
                    'status': statusdict,
                    'can_delete': has_permission(request, 'delete_any_workflow') or is_creator
                })

            context.update({'workflow_cards': workflow_cards})
            return context

        finally:
            session.close()

    def post(self, request, resource_id, *args, **kwargs):
        """
        Handle forms on resource details page.
        """
        params = request.POST

        if 'new-workflow' in params:
            # Params
            workflow_name = params.get('workflow-name', '')
            workflow_type = params.get('workflow-type', '')

            if not workflow_name:
                messages.error(request, 'Unable to create new workflow: no name given.')
                return self.get(request, resource_id, *args, **kwargs)

            if not workflow_type or workflow_type not in self.resource_workflows:
                messages.error(request, 'Unable to create new workflow: invalid workflow type.')
                return self.get(request, resource_id, *args, **kwargs)

            # Create new workflow
            _AppUser = self.get_app_user_model()
            make_session = self.get_sessionmaker()
            session = make_session()
            request_app_user = _AppUser.get_app_user_from_request(request, session)

            try:
                WorkflowModel = self.resource_workflows[workflow_type]
                workflow_app = self._app
                workflow = WorkflowModel.new(
                    app=workflow_app,
                    name=workflow_name,
                    resource_id=resource_id,
                    creator_id=request_app_user.id,
                    geoserver_name=workflow_app.GEOSERVER_NAME,
                    map_manager=self.get_map_manager(),
                    spatial_manager=self.get_spatial_manager(),
                )
                session.add(workflow)
                session.commit()

            except Exception:
                message = 'An unexpected error occurred while creating the new workflow.'
                log.exception(message)
                messages.error(request, message)
                return self.get(request, resource_id, *args, **kwargs)
            finally:
                session.close()

            messages.success(request, 'Successfully created new {}: {}'.format(
                self.resource_workflows[workflow_type].DISPLAY_TYPE_SINGULAR, workflow_name)
                             )
            return self.get(request, resource_id, *args, **kwargs)

        # Redirect/render the normal GET page by default with warning message.
        messages.warning(request, 'Unable to perform requested action.')
        return self.get(request, resource_id, *args, **kwargs)

    def delete(self, request, resource_id, *args, **kwargs):
        """
        Handle delete requests.
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
