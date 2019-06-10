"""
********************************************************************************
* Name: resource_workflow_step
* Author: nswain
* Created On: November 19, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json
import uuid
from abc import abstractmethod
from copy import deepcopy

from sqlalchemy import Column, ForeignKey, String, PickleType, Integer
from sqlalchemy.orm import relationship, backref
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, OptionsMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.controller_metadata import ControllerMetadata


__all__ = ['ResourceWorkflowStep']


class ResourceWorkflowStep(AppUsersBase, StatusMixin, AttributesMixin, OptionsMixin):
    """
    Data model for storing information about resource workflows.

    Primary Workflow Step Status Progression:
    1. STATUS_PENDING = Step has not been started yet.
    2. STATUS_WORKING = Processing on step has been started but not complete.
    3. STATUS_ERROR = ValueError or ValidateError has occurred.
    4. STATUS_FAILED = Processing error has occurred.
    5. STATUS_COMPLETE = Step has been completed successfully.
    """
    __tablename__ = 'app_users_resource_workflow_steps'
    CONTROLLER = ''
    TYPE = 'generic_workflow_step'
    ATTR_STATUS_MESSAGE = 'status_message'
    OPT_PARENT_STEP = 'parent'
    UUID_FIELDS = ['id', 'child_id', 'resource_workflow_id']
    SERIALIZED_FIELDS = ['id', 'child_id', 'resource_workflow_id', 'type', 'name', 'help']

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    child_id = Column(GUID, ForeignKey('app_users_resource_workflow_steps.id'))
    result_id = Column(GUID, ForeignKey('app_users_resource_workflow_steps.id'))
    controller_metadata_id = Column(GUID, ForeignKey('app_users_controller_metadata.id'))
    resource_workflow_id = Column(GUID, ForeignKey('app_users_resource_workflows.id'))
    type = Column(String)

    name = Column(String)
    help = Column(String)
    order = Column(Integer)
    status = Column(String)
    _options = Column(PickleType, default={})
    _attributes = Column(String)
    _parameters = Column(PickleType, default={})

    _controller = relationship(
        'ControllerMetadata',
        backref='step',
        cascade='all,delete',
        uselist=False,
    )

    child = relationship(
        'ResourceWorkflowStep',
        backref=backref('parent', uselist=False),
        foreign_keys=[child_id],
        remote_side=[id],
        cascade='all,delete'
    )

    result = relationship(
        'ResultsResourceWorkflowStep',
        backref=backref('source', uselist=False),
        foreign_keys=[result_id],
        remote_side=[id],
        cascade='all,delete'
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial status
        self.set_status(self.ROOT_STATUS_KEY, self.STATUS_PENDING)

        # Initialize parameters
        if not self._parameters:
            self._parameters = self.init_parameters(*args, **kwargs)

        if 'options' in kwargs:
            self.options = kwargs['options']
        else:
            self._options = self.default_options

        self._controller = ControllerMetadata(path=self.CONTROLLER)

    def __str__(self):
        return '<{} name="{}" id="{}" >'.format(self.__class__.__name__, self.name, self.id)

    def __repr__(self):
        return self.__str__()

    @property
    def controller(self):
        return self._controller

    @abstractmethod
    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.
        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """

    def to_dict(self):
        """
        Serialize ResourceWorkflowStep into a dictionary.

        Returns:
            dict: dictionary representation of ResourceWorkflowStep.
        """
        d = {}

        for k, v in self.__dict__.items():
            if k in self.SERIALIZED_FIELDS and k[0] != '_':
                if k in self.UUID_FIELDS:
                    d.update({k: str(v)})
                else:
                    d.update({k: v})

        parameters = {}
        for param, data in self.get_parameters().items():
            parameters.update({param: data['value']})

        d.update({'parameters': parameters})
        return d

    def to_json(self):
        """
        Serialize ResourceWorkflowStep, including parameters, to json.

        Returns:
            str: JSON string representation of ResourceWorkflowStep.
        """
        return json.dumps(self.to_dict())

    def validate(self):
        """
        Validates parameter values of this this step. If the parameter values of this step are invalid a ValueError will be raised
        """  # noqa: E501
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
        dc_parameters = deepcopy(self._parameters)
        dc_parameters[name]['value'] = value
        self._parameters = dc_parameters

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
            raise ValueError('No parameter named "{}" in step "{}".'.format(name, self))

    def get_parameters(self):
        """
        Get all parameter objects.
        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return deepcopy(self._parameters)

    def resolve_option(self, option):
        """
        Resolve options that depend on parameters from other steps.
        """
        option_value = self.options.get(option, None)

        if option_value is None:
            return None

        if isinstance(option_value, dict) and self.OPT_PARENT_STEP in option_value:
            field_name = option_value[self.OPT_PARENT_STEP]
            parent_step = self.parent

            try:
                parent_parameter = parent_step.get_parameter(field_name)
                return parent_parameter
            except ValueError as e:
                raise RuntimeError(str(e))
