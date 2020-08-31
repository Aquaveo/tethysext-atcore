"""
********************************************************************************
* Name: resource_workflow.py
* Author: nswain
* Created On: September 25, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import uuid
import logging
import datetime as dt
from abc import abstractmethod

from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import AttributesMixin, ResultsMixin, UserLockMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.app_users import ResourceWorkflowStep


log = logging.getLogger(__name__)
__all__ = ['ResourceWorkflow']


class ResourceWorkflow(AppUsersBase, AttributesMixin, ResultsMixin, UserLockMixin):
    """
    Data model for storing information about resource workflows.

    Primary Workflow Status Progression:
    1. STATUS_PENDING = No steps have been started in workflow.
    2. STATUS_CONTINUE = Workflow has non-complete steps, has no steps with errors or failed, and no steps that are processing.
    3. STATUS_WORKING = Workflow has steps that are processing.
    4. STATUS_ERROR = Workflow has steps with errors.test_get_status_options_list
    5. STATUS_FAILED = Workflow has steps that have failed.
    6. STATUS_COMPLETE = All steps are complete in workflow.

    Review Workflow Status Progression (if applicable):
    1. STATUS_SUBMITTED = Workflow submitted for review
    2. STATUS_UNDER_REVIEW = Workflow currently being reviewed
    3a. STATUS_APPROVED = Changes approved.
    3b. STATUS_REJECTED = Changes disapproved.
    3c. STATUS_CHANGES_REQUESTED = Changes required and resubmit
    """  # noqa: E501
    __tablename__ = 'app_users_resource_workflows'

    TYPE = 'generic_workflow'
    DISPLAY_TYPE_SINGULAR = 'Generic Workflow'
    DISPLAY_TYPE_PLURAL = 'Generic Workflows'

    STATUS_PENDING = ResourceWorkflowStep.STATUS_PENDING
    STATUS_CONTINUE = ResourceWorkflowStep.STATUS_CONTINUE
    STATUS_WORKING = ResourceWorkflowStep.STATUS_WORKING
    STATUS_COMPLETE = ResourceWorkflowStep.STATUS_COMPLETE
    STATUS_FAILED = ResourceWorkflowStep.STATUS_FAILED
    STATUS_ERROR = ResourceWorkflowStep.STATUS_ERROR

    STATUS_SUBMITTED = ResourceWorkflowStep.STATUS_SUBMITTED
    STATUS_UNDER_REVIEW = ResourceWorkflowStep.STATUS_UNDER_REVIEW
    STATUS_APPROVED = ResourceWorkflowStep.STATUS_APPROVED
    STATUS_REJECTED = ResourceWorkflowStep.STATUS_REJECTED
    STATUS_CHANGES_REQUESTED = ResourceWorkflowStep.STATUS_CHANGES_REQUESTED
    STATUS_REVIEWED = ResourceWorkflowStep.STATUS_REVIEWED

    COMPLETE_STATUSES = ResourceWorkflowStep.COMPLETE_STATUSES

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    resource_id = Column(GUID, ForeignKey('app_users_resources.id'))
    creator_id = Column(GUID, ForeignKey('app_users_app_users.id'))
    type = Column(String)

    name = Column(String)
    date_created = Column(DateTime, default=dt.datetime.utcnow)
    lock_when_finished = Column(Boolean, default=False)
    _attributes = Column(String)
    _user_lock = Column(String)

    resource = relationship('Resource', backref=backref('workflows', cascade='all,delete'))
    creator = relationship('AppUser', backref='workflows')
    steps = relationship('ResourceWorkflowStep', order_by='ResourceWorkflowStep.order', backref='workflow',
                         cascade='all,delete')
    results = relationship('ResourceWorkflowResult', order_by='ResourceWorkflowResult.order', backref='workflow',
                           cascade='all,delete')

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __repr__(self):
        return f'<{self.__class__.__name__} name="{self.name}" id="{self.id}" locked={self.is_user_locked}>'

    @property
    def complete(self):
        return self.get_status() in self.COMPLETE_STATUSES

    def get_next_step(self):
        """
        Return the next step object, based on the status of the steps.

        Returns:
            int, ResourceWorkflowStep: the index of the next step and the next step.
        """
        idx = 0
        step = None

        for idx, step in enumerate(self.steps):
            if not step.complete:
                return idx, step

        # Return last step and index if none complete
        return idx, step

    def get_status(self):
        """
        Returns the status of the next workflow step.

        Returns:
            ResourceWorkflowStep.STATUS_X: status of the next step.
        """
        index, next_step = self.get_next_step()
        # TODO: Handle when next step is None or all complete = show results
        status = next_step.get_status(ResourceWorkflowStep.ROOT_STATUS_KEY) \
            if next_step else ResourceWorkflowStep.STATUS_NONE

        # If we are not on the first step and the status is pending, workflow status is continue
        if status == ResourceWorkflowStep.STATUS_PENDING and index > 0:
            return self.STATUS_CONTINUE

        return status

    def get_adjacent_steps(self, step):
        """
        Get the adjacent steps to the given step.

        Args:
            step(ResourceWorkflowStep): A step belonging to this workflow.

        Returns:
            ResourceWorkflowStep, ResourceWorkflowStep: previous and next steps, respectively.
        """
        if step not in self.steps:
            raise ValueError('Step {} does not belong to this workflow.'.format(step))

        index = self.steps.index(step)
        previous_index = index - 1
        next_index = index + 1
        previous_step = self.steps[previous_index] if previous_index >= 0 else None
        next_step = self.steps[next_index] if next_index < len(self.steps) else None

        return previous_step, next_step

    def get_previous_steps(self, step):
        """
        Get all previous steps to the given step.

        Args:
           step(ResourceWorkflowStep): A step belonging to this workflow.

        Returns:
            list<ResourceWorkflowStep>: a list of steps previous to this one.
        """
        if step not in self.steps:
            raise ValueError('Step {} does not belong to this workflow.'.format(step))

        step_index = self.steps.index(step)
        previous_steps = self.steps[:step_index]
        return previous_steps

    def get_next_steps(self, step):
        """
        Get all steps following the given step.
        Args:
            step(ResourceWorkflowStep): A step belonging to this workflow.

        Returns:
            list<ResourceWorkflowStep>: a list of steps following this one.
        """
        if step not in self.steps:
            raise ValueError('Step {} does not belong to this workflow.'.format(step))

        step_index = self.steps.index(step)
        next_steps = self.steps[step_index + 1:]
        return next_steps

    def reset_next_steps(self, step, include_current=False):
        """
        Reset all steps following the given step that are not PENDING.
        Args:
            step(ResourceWorkflowStep): A step belonging to this workflow.
            include_current(bool): Reset current step
        """
        if step not in self.steps:
            raise ValueError('Step {} does not belong to this workflow.'.format(step))

        next_steps = self.get_next_steps(step)

        for s in next_steps:
            # Only reset if the step is not in pending status
            status = s.get_status(s.ROOT_STATUS_KEY)
            if status != s.STATUS_PENDING:
                s.reset()

        if include_current:
            step.reset()

    @abstractmethod
    def get_url_name(self):
        pass
