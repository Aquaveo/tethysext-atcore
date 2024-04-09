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

from sqlalchemy import Column, ForeignKey, String, PickleType, Integer, Boolean
from sqlalchemy.orm import relationship, backref
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, OptionsMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.app_users.associations import step_parent_child_association
from tethysext.atcore.models.controller_metadata import ControllerMetadata
from tethysext.atcore.utilities import json_serializer

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

    Review Workflow Status Progression (if applicable):
    1. STATUS_SUBMITTED = Workflow submitted for review
    2. STATUS_UNDER_REVIEW = Workflow currently being reviewed
    3a. STATUS_APPROVED = Changes approved.
    3b. STATUS_REJECTED = Changes disapproved.
    3c. STATUS_CHANGES_REQUESTED = Changes required and resubmit

    Options:
        workflow_lock_required(bool): This step requires a workflow lock to be performed (to prevent conflicts). Defaults to False.
        release_workflow_lock_on_completion(bool): Attempt to release a workflow lock when the view is initialized. Defaults to True.
        release_workflow_lock_on_init(bool): Attempt to release a workflow lock when the step is completed. Ignored if `workflow_lock_required` is True. Defaults to False.
        resource_lock_required(bool): This step requires a resource lock to be performed (to prevent conflicts). Defaults to False.
        release_resource_lock_on_completion(bool): Attempt to release a resource lock when the view is initialized. Defaults to True.
        release_resource_lock_on_init(bool): Attempt to release a resource lock when the step is completed. Ignored if `resource_lock_required` is True. Defaults to False.
    """  # noqa: E501
    __tablename__ = 'app_users_resource_workflow_steps'
    CONTROLLER = ''
    TYPE = 'generic_workflow_step'
    ATTR_STATUS_MESSAGE = 'status_message'
    OPT_PARENT_STEP = 'parent'
    UUID_FIELDS = ['id', 'child_id', 'resource_workflow_id']
    SERIALIZED_FIELDS = ['id', 'child_id', 'resource_workflow_id', 'type', 'name', 'help']

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    result_id = Column(GUID, ForeignKey('app_users_resource_workflow_steps.id'))
    controller_metadata_id = Column(GUID, ForeignKey('app_users_controller_metadata.id'))
    resource_workflow_id = Column(GUID, ForeignKey('app_users_resource_workflows.id'))
    type = Column(String)

    name = Column(String)
    help = Column(String)
    order = Column(Integer)
    status = Column(String)
    dirty = Column(Boolean, default=False)
    _options = Column(PickleType, default={})
    _attributes = Column(String)
    _parameters = Column(PickleType, default={})
    _active_roles = Column(PickleType, default=[])

    _controller = relationship(
        'ControllerMetadata',
        backref='step',
        cascade='all,delete',
        uselist=False,
    )

    children = relationship(
        'ResourceWorkflowStep',
        secondary=step_parent_child_association,
        backref=backref('parents'),
        secondaryjoin=id == step_parent_child_association.c.child_id,
        primaryjoin=id == step_parent_child_association.c.parent_id,
        cascade='all,delete',
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

        if 'active_roles' in kwargs:
            self.active_roles = kwargs['active_roles']

        self._controller = ControllerMetadata(path=self.CONTROLLER)

    def __str__(self):
        return '<{} name="{}" id="{}" >'.format(self.__class__.__name__, self.name, self.id)

    def __repr__(self):
        return self.__str__()

    @property
    def default_options(self):
        """
        Returns default options dictionary for the object.
        """  # noqa: E501
        return {
            'workflow_lock_required': False,
            'release_workflow_lock_on_completion': True,
            'release_workflow_lock_on_init': False,
            'resource_lock_required': False,
            'release_resource_lock_on_completion': True,
            'release_resource_lock_on_init': False
        }

    @property
    def complete(self):
        return self.get_status(default=self.STATUS_PENDING) in self.COMPLETE_STATUSES

    @property
    def active_roles(self):
        return self._active_roles

    @active_roles.setter
    def active_roles(self, value):
        if not isinstance(value, list) or not all(isinstance(elem, str) for elem in value):
            raise ValueError(f'Property "active_roles" must be a list of strings. Got "{value}" instead.')
        self._active_roles = value

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

    @classmethod
    def valid_statuses(cls):
        """
        Primary Workflow Step Status Progression:
        1. STATUS_PENDING = Step has not been started yet.
        2. STATUS_WORKING = Processing on step has been started but not complete.
        3. STATUS_ERROR = ValueError or ValidateError has occurred.
        4. STATUS_FAILED = Processing error has occurred.
        5. STATUS_COMPLETE = Step has been completed successfully.

        Review Workflow Status Progression (if applicable):
        1. STATUS_SUBMITTED = Workflow submitted for review.
        2. STATUS_UNDER_REVIEW = Workflow currently being reviewed.
        3a. STATUS_APPROVED = Changes approved.
        3b. STATUS_REJECTED = Changes disapproved.
        3c. STATUS_CHANGES_REQUESTED = Changes required and resubmit.
        4. STATUS_REVIEWED - Workflow has been reviewed.

        Returns:
            list: valid statuses.
        """
        return [cls.STATUS_PENDING, cls.STATUS_WORKING, cls.STATUS_ERROR, cls.STATUS_FAILED, cls.STATUS_COMPLETE,
                cls.STATUS_SUBMITTED, cls.STATUS_UNDER_REVIEW, cls.STATUS_APPROVED, cls.STATUS_REJECTED,
                cls.STATUS_CHANGES_REQUESTED, cls.STATUS_REVIEWED]

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
        return json.dumps(self.to_dict(), default=json_serializer)

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

        if dc_parameters != self._parameters:
            self.dirty = True

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
            parent_options = option_value[self.OPT_PARENT_STEP]
            parent_field = parent_options.get('parent_field', 'geometry')

            # Get match criteria, if any
            match_attr = parent_options.get('match_attr', None)
            match_value = parent_options.get('match_value', None)

            target_parent = None

            if match_attr is not None and match_value is not None:
                # Find the parent that matches the given criteria
                for parent in self.parents:
                    if getattr(parent, match_attr, None) == match_value:
                        target_parent = parent
                        break
            else:
                # Default to the first parent if no match criteria given
                try:
                    target_parent = self.parents[0]
                except IndexError:
                    raise RuntimeError('Cannot resolve option from parent: no parents found.')

            # Get the parameter from the parent identified
            if target_parent:
                try:
                    parent_parameter = target_parent.get_parameter(parent_field)
                    return parent_parameter
                except ValueError as e:
                    raise RuntimeError(str(e))

            raise RuntimeError('Cannot resolve option from parent: no parents match criteria given.')

    def reset(self):
        """
        Resets the step back to its initial state.
        """
        # Reset status
        self.set_status(self.ROOT_STATUS_KEY, self.STATUS_PENDING)

        # Reset parameters
        self._parameters = self.init_parameters()

        # Reset dirty
        self.dirty = False
