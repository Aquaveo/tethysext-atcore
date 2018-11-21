"""
********************************************************************************
* Name: resource_workflow_step
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import inspect
import uuid

from sqlalchemy import Column, ForeignKey, String, PickleType
from tethys_sdk.base import TethysController
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin
from tethysext.atcore.models.app_users.base import AppUsersBase


__all__ = ['ResourceWorkflowStep']


class ResourceWorkflowStep(AppUsersBase, StatusMixin, AttributesMixin):
    """
    Data model for storing information about resource workflows.

    Primary Workflow Step Status Progression:
    1. STATUS_PENDING = Step has not been started yet.
    2. STATUS_WORKING = Step has has beens started but not complete.
    3. STATUS_ERROR = ValueError or ValidateError has occured.
    4. STATUS_FAILED = ProcessingError has occured.
    5. STATUS_COMPLETE = Step has been completed successfully.
    """
    __tablename__ = 'app_users_resource_workflow_steps'

    TYPE = 'generic_workflow_step'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    resource_workflow_id = Column(GUID, ForeignKey('app_users_resource_workflows.id'))
    type = Column(String)

    name = Column(String)
    help = Column(String)
    http_methods = Column(PickleType, default=['get', 'post', 'delete'])
    controller_path = Column(String)
    controller_kwargs = Column(PickleType, default={})
    status = Column(String)
    _attributes = Column(String)

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        super(ResourceWorkflowStep, self).__init__(*args, **kwargs)

        # Set initial status
        self.set_status(self.ROOT_STATUS_KEY, self.STATUS_PENDING)

    def get_controller(self, **kwargs):
        """
        Get the controller method from the given controller_name.
        Args:
            kwargs: any kwargs that would be passed to the get_controller method of TethysControllers (i.e.: class-based view property overrides).

        Returns:
            function: the controller method.
        """  # noqa: E501
        from tethysext.atcore.controllers.app_users.base import AppUsersResourceController
        from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController

        try:
            # Split into parts and extract function name
            module_path, controller_name = self.controller_path.rsplit('.', 1)

            # Import module
            module = __import__(module_path, fromlist=[str(controller_name)])

        except (ValueError, ImportError):
            raise ImportError('Unable to import controller: {}'.format(self.controller_path))

        # Import the function or class
        controller = getattr(module, controller_name)

        # Get entry point for class based views
        if inspect.isclass(controller) and issubclass(controller, TethysController):
            # Call with all kwargs if is instance of an AppUsersResourceWorkflowController
            if issubclass(controller, AppUsersResourceWorkflowController):
                kwargs.update(self.controller_kwargs)
                controller = controller.as_controller(**kwargs)

            # Call with all but workflow kwargs if AppUsersResourceController
            elif issubclass(controller, AppUsersResourceController):
                kwargs.pop('_ResourceWorkflow')
                kwargs.pop('_ResourceWorkflowStep')
                kwargs.update(self.controller_kwargs)
                controller = controller.as_controller(**kwargs)

            # Otherwise, don't call with any kwargs
            else:
                controller = controller.as_controller(**self.controller_kwargs)

        return controller
