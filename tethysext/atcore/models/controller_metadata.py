"""
********************************************************************************
* Name: controller_metadata
* Author: nswain
* Created On: April 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import inspect
import uuid

from sqlalchemy import Column, String, PickleType
from tethys_sdk.base import TethysController
from tethysext.atcore.models.types import GUID
from tethysext.atcore.models.app_users.base import AppUsersBase

__all__ = ['ControllerMetadata']


class ControllerMetadata(AppUsersBase):
    """
    Data model that stores controller metadata for objects associated with controllers.
    """
    __tablename__ = 'app_users_controller_metadata'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    path = Column(String)
    kwargs = Column(PickleType, default={})
    http_methods = Column(PickleType, default=['get', 'post', 'delete'])

    def instantiate(self, **kwargs):
        """
        Instantiate an instance of the TethysController referenced by the path with the given kwargs.

        Args:
            kwargs: any kwargs that would be passed to the as_controller method of TethysControllers (i.e.: class-based view property overrides).

        Returns:
            function: the controller method.
        """  # noqa: E501
        from tethysext.atcore.controllers.app_users.base import AppUsersResourceController
        from tethysext.atcore.controllers.resource_workflows.base import AppUsersResourceWorkflowController

        try:
            # Split into parts and extract function name
            module_path, controller_name = self.path.rsplit('.', 1)

            # Import module
            module = __import__(module_path, fromlist=[str(controller_name)])

        except (ValueError, ImportError):
            raise ImportError('Unable to import controller: {}'.format(self.path))

        # Import the function or class
        controller = getattr(module, controller_name)

        # Get entry point for class based views
        if inspect.isclass(controller) and issubclass(controller, TethysController):
            # Call with all kwargs if is instance of an AppUsersResourceWorkflowController
            if issubclass(controller, AppUsersResourceWorkflowController):
                kwargs.update(self.kwargs)
                controller = controller.as_controller(**kwargs)

            # Call with all but workflow kwargs if AppUsersResourceController
            elif issubclass(controller, AppUsersResourceController):
                kwargs.pop('_ResourceWorkflow')
                kwargs.pop('_ResourceWorkflowStep')
                kwargs.update(self.kwargs)
                controller = controller.as_controller(**kwargs)

            # Otherwise, don't call with any kwargs
            else:
                controller = controller.as_controller(**self.kwargs)

        return controller
