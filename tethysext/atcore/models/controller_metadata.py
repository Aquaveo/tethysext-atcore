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
from tethysext.atcore.models.types import GUID
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.utilities import import_from_string

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
        from tethys_sdk.base import TethysController
        from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
        from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView

        try:
            controller = import_from_string(self.path)

        except (ValueError, AttributeError, ImportError) as e:
            raise ImportError(f'Unable to import controller "{self.path}": {e}')

        # Get entry point for class based views
        if inspect.isclass(controller) and issubclass(controller, TethysController):
            # Call with all kwargs if is instance of an ResourceWorkflowView
            if issubclass(controller, ResourceWorkflowView):
                kwargs.update(self.kwargs)
                controller = controller.as_controller(**kwargs)

            # Call with all but workflow kwargs if ResourceView
            elif issubclass(controller, ResourceViewMixin):
                kwargs.pop('_ResourceWorkflow', None)
                kwargs.pop('_ResourceWorkflowStep', None)
                kwargs.update(self.kwargs)
                controller = controller.as_controller(**kwargs)

            # Otherwise, don't call with any kwargs
            else:
                kwargs.update(self.kwargs)
                controller = controller.as_controller(**kwargs)

        return controller
