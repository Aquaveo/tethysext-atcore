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
from abc import abstractmethod
from copy import deepcopy

from sqlalchemy import Column, ForeignKey, String, PickleType, Integer
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
    order = Column(Integer)
    options = Column(PickleType, default={})
    http_methods = Column(PickleType, default=['get', 'post', 'delete'])
    controller_path = Column(String)
    controller_kwargs = Column(PickleType, default={})
    status = Column(String)
    _attributes = Column(String)
    _parameters = Column(PickleType, default={})

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        super(ResourceWorkflowStep, self).__init__(*args, **kwargs)

        # Set initial status
        self.set_status(self.ROOT_STATUS_KEY, self.STATUS_PENDING)

        # Initialize parameters
        if not self._parameters:
            self._parameters = self.init_parameters(*args, **kwargs)

    def __str__(self):
        return '<{} id={} name={}>'.format(self.__class__, self.id, self.name)

    @abstractmethod
    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.
        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """

    def validate(self):
        """
        Validates parameter values of this this step.
        Returns:
            bool: True if data is valid, else False.
        """
        params = self._parameters

        # Check Required
        for name, param in params.items():
            if param['required'] and not param['value']:
                raise ValueError('Parameter "{}" is required.'.format(name))

    def parse_parameters(self, parameters):
        """
        Parse parameters from a dictionary.

        Args:
            parameters(dict<name,value>): Dictionary of parameters.
        """
        for name, value in parameters.items():
            try:
                self.set_parameter(name, value)
            except ValueError:
                pass  # Ignore parameters that don't exist when parsing.

    def set_parameter(self, name, value):
        """
        Sets the value of the named parameter.
        Args:
            name(str): Name of the parameter to set.
            value(varies): Value of the parameter.
        """
        if name not in self._parameters:
            raise ValueError('No parameter named "{}" in this step.'.format(name))

        # Must copy the entire parameters dict, make changes to the copy,
        # and overwrite to get sqlalchemy to recognize a change has occurred,
        # and propagate the changes to the database.
        old_parameters = deepcopy(self._parameters)
        old_parameters[name]['value'] = value
        self._parameters = old_parameters

    def get_parameter(self, name):
        """
        Get value of the named parameter.
        Args:
            name(str): name of parameter.

        Returns:
            varies: Value of the named parameter.
        """
        try:
            return self._parameters[name]['value']
        except KeyError:
            raise ValueError('No parameter named "{}" in this step.'.format(name))

    def get_parameters(self):
        """
        Get all parameter objects.
        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return deepcopy(self._parameters)

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
