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
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Session
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import AttributesMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.app_users import ResourceWorkflowStep, ResourceWorkflowResult


log = logging.getLogger(__name__)
__all__ = ['ResourceWorkflow']


class ResourceWorkflow(AppUsersBase, AttributesMixin):
    """
    Data model for storing information about resource workflows.

    Primary Workflow Status Progression:
    1. STATUS_PENDING = No steps have been started in workflow.
    2. STATUS_CONTINUE = Workflow has non-complete steps, has no steps with errors or failed, and no steps that are processing.
    2. STATUS_WORKING = Workflow has steps that are processing.
    3. STATUS_ERROR = Workflow has steps with errors.test_get_status_options_list
    4. STATUS_FAILED = Workflow has steps that have failed.
    5. STATUS_COMPLETE = All steps are complete in workflow.
    """  # noqa: E501
    __tablename__ = 'app_users_resource_workflows'

    TYPE = 'generic_workflow'
    DISPLAY_TYPE_SINGULAR = 'Generic Workflow'
    DISPLAY_TYPE_PLURAL = 'Generic Workflows'
    ATTR_LAST_RESULT = 'last_result'

    STATUS_PENDING = ResourceWorkflowStep.STATUS_PENDING
    STATUS_CONTINUE = ResourceWorkflowStep.STATUS_CONTINUE
    STATUS_WORKING = ResourceWorkflowStep.STATUS_WORKING
    STATUS_COMPLETE = ResourceWorkflowStep.STATUS_COMPLETE
    STATUS_FAILED = ResourceWorkflowStep.STATUS_FAILED
    STATUS_ERROR = ResourceWorkflowStep.STATUS_ERROR

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    resource_id = Column(GUID, ForeignKey('app_users_resources.id'))
    creator_id = Column(GUID, ForeignKey('app_users_app_users.id'))
    type = Column(String)

    name = Column(String)
    date_created = Column(DateTime, default=dt.datetime.utcnow)
    _attributes = Column(String)

    resource = relationship('Resource', backref='workflows')
    creator = relationship('AppUser', backref='workflows')
    steps = relationship('ResourceWorkflowStep', order_by='ResourceWorkflowStep.order', backref='workflow')
    results = relationship('ResourceWorkflowResult', order_by='ResourceWorkflowResult.order', backref='workflow')

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __str__(self):
        return '<{} id={} name={}>'.format(self.__class__.__name__, self.id, self.name)

    def get_next_step(self):
        """
        Return the next step object, based on the status of the steps.

        Returns:
            int, ResourceWorkflowStep: the index of the next step and the next step.
        """
        idx = 0
        step = None

        for idx, step in enumerate(self.steps):
            step_status = step.get_status(step.ROOT_STATUS_KEY, step.STATUS_PENDING)

            if step_status != ResourceWorkflowStep.STATUS_COMPLETE:
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

    def get_last_result(self):
        """
        Get the result which was last viewed by the user.

        Args:
            session(sqlalchemy.Session): the session.

        Returns:
            ResourceWorkflowResult: the last result or None if not found.
        """
        try:
            session = Session.object_session(self)
            last_result_id = self.get_attribute(self.ATTR_LAST_RESULT)
            if last_result_id is not None:
                # Load the previously viewed result?
                result = session.query(ResourceWorkflowResult).get(last_result_id)

                if result is None:
                    log.warning('Result with id "{}" not in workflow'.format(last_result_id))
                return result

            return self.results[0]
        except (IndexError, AttributeError) as e:
            if isinstance(e, IndexError):
                log.warning('Workflow has no results.')
            elif isinstance(e, AttributeError):
                log.error('Could not get session from workflow: {}'.format(str(e)))
            return None

    def set_last_result(self, result=None):
        """
        Set the id of the last result viewed by the user.

        Args:
           result(ResourceWorkflowResult): The result to mark as being last viewed.

        """
        if result not in self.results:
            raise ValueError('Result provided must belong to this workflow.')
        return self.set_attribute(self.ATTR_LAST_RESULT, str(result.id))

    def get_adjacent_results(self, result):
        """
        Get the adjacent results the given result.

        Args:
            result(ResourceWorkflowResult): A result belonging to this workflow.

        Returns:
            ResourceWorkflowResult, ResourceWorkflowResult: previous and next results, respectively.
        """
        if result not in self.results:
            raise ValueError('Result {} does not belong to this workflow.'.format(result))

        index = self.results.index(result)
        previous_index = index - 1
        next_index = index + 1
        previous_result = self.results[previous_index] if previous_index >= 0 else None
        next_result = self.results[next_index] if next_index < len(self.results) else None
        return previous_result, next_result
