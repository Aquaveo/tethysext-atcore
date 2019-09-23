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
from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import AttributesMixin, ResultsMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.app_users import ResourceWorkflowStep


log = logging.getLogger(__name__)
__all__ = ['ResourceWorkflow']


class ResourceWorkflow(AppUsersBase, AttributesMixin, ResultsMixin):
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

    COMPLETE_STATUSES = ResourceWorkflowStep.COMPLETE_STATUSES

    LOCKED_FOR_ALL_USERS = '__locked_for_all_users__'

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
        return f'<{self.__class__.__name__} name="{self.name}" id="{self.id}">'

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
        status = next_step.get_status(ResourceWorkflowStep.ROOT_STATUS_KEY)

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

    def reset_next_steps(self, step):
        """
        Reset all steps following the given step that are not PENDING.
        Args:
            step(ResourceWorkflowStep): A step belonging to this workflow.
        """
        if step not in self.steps:
            raise ValueError('Step {} does not belong to this workflow.'.format(step))

        next_steps = self.get_next_steps(step)

        for s in next_steps:
            # Only reset if the step is not in pending status
            status = s.get_status(s.ROOT_STATUS_KEY)
            if status != s.STATUS_PENDING:
                s.reset()

    def acquire_user_lock(self, request=None):
        """
        Acquire a user lock for the given request user. Only the given user will be able to access the workflow in read-write mode. All other users will have read-only access. If no user is provided, the workflow will be locked for all users.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if acquisition was successful. False if already locked.
        """  # noqa: E501
        lock_acquired = False
        already_locked = self.is_user_locked

        if request is None:
            if not already_locked:
                self._user_lock = self.LOCKED_FOR_ALL_USERS
                lock_acquired = True
            # if already locked and ...
            elif self.is_locked_for_all_users:
                lock_acquired = True

        else:  # request given
            if not already_locked:
                self._user_lock = request.user.username
                lock_acquired = True
            # if already locked and ...
            elif self.user_lock == request.user.username:
                lock_acquired = True

        return lock_acquired

    def release_user_lock(self, request):
        """
        Release the user lock for the request user user. Only the user that was used to acquire the lock or other user with appropriate permissions (e.g. admin or staff user) can release a user lock. If the workflow is locked for all users, an admin will be required to unlock it.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if release was successful or if the user lock was not locked. False otherwise.
        """  # noqa: E501
        from tethys_sdk.permissions import has_permission

        lock_released = False
        can_override = has_permission(request, 'can_override_user_locks')

        if not self.is_user_locked:
            # lock is already unlocked
            lock_released = True
        elif self.is_locked_for_all_users and can_override:
            # lock is locked for all uses and can only be unlocked by users with override permissions
            self._user_lock = None
            lock_released = True
        elif self.user_lock == request.user.username:
            # lock is locked for the given user
            self._user_lock = None
            lock_released = True
        elif can_override:
            # lock is locked, not for all users or the given user, but user has override permissions
            self._user_lock = None
            lock_released = True

        return lock_released

    @property
    def user_lock(self):
        """
        Get the current value of the user lock.

        Returns:
            str or None: the username of the user that has read-write access, LOCKED_FOR_ALL_USERS if locked for all users, or None if the user lock is not locked.
        """  # noqa: E501
        return self._user_lock

    @property
    def is_user_locked(self):
        """
        Check if the workflow is user locked.

        Returns:
            bool: True if the workflow is user locked, False if not.
        """
        return self._user_lock is not None and self._user_lock != ''

    @property
    def is_locked_for_all_users(self):
        """
        Check if the workflow is user locked for all users.

        Returns:
            bool: True if the workflow is user locked for all users, False if not.
        """  # noqa: E501
        return self._user_lock == self.LOCKED_FOR_ALL_USERS

    def is_locked_for_request_user(self, request):
        """
        Determine if the lock is locked for the request user.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if workflow is locked for request user.
        """
        from tethys_sdk.permissions import has_permission

        if has_permission(request, 'can_override_user_locks'):
            return False

        return self.is_user_locked and self._user_lock != request.user.username
