"""
********************************************************************************
* Name: map_workflow_view.py
* Author: nswain
* Created On: November 21, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.shortcuts import redirect
from django.contrib import messages
from tethysext.atcore.exceptions import ATCoreException
from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController
from tethysext.atcore.controllers.map_view import MapView


class MapWorkflowView(MapView, AppUsersResourceWorkflowController):
    """
    Controller for a map view with workflows integration.
    """
    template_name = 'atcore/resource_workflows/map_workflow_view.html'

    def get_context(self, request, context, model_db, map_manager, workflow_id, step_id, *args, **kwargs):
        """
        Get workflow and steps and add to the context.

        Args:
            request (HttpRequest): The request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.
            map_manager (MapManager): MapManager instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        _ResourceWorkflow = self.get_resource_workflow_model()
        session = None

        try:
            make_session = self.get_sessionmaker()
            session = make_session()
            workflow = self.get_workflow(request, workflow_id, session=session)

            context.update({
                'workflow': workflow,
                'steps': workflow.steps,
                'map_title': workflow.name,
                'map_subtitle': workflow.DISPLAY_TYPE_SINGULAR
            })

        except (StatementError, NoResultFound):
            messages.warning(request, 'The {} could not be found.'.format(
                _ResourceWorkflow.DISPLAY_TYPE_SINGULAR.lower()
            ))
            return redirect(self.back_url)
        except ATCoreException as e:
            error_message = str(e)
            messages.warning(request, error_message)
            return redirect(self.back_url)
        finally:
            session and session.close()

        return context
