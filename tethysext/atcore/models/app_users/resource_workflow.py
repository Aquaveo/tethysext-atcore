"""
********************************************************************************
* Name: resource_workflow.py
* Author: nswain
* Created On: September 25, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import uuid
import datetime as dt
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import AttributesMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep


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
    steps = relationship('ResourceWorkflowStep', backref='workflow')

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def get_next_step(self):
        """
        Return the next step object, based on the status of the steps.

        Returns:
            int, ResourceWorkflowStep: the index of the next step and the next step.
        """
        for idx, step in enumerate(self.steps):
            step_status = step.get_status(
                ResourceWorkflowStep.ROOT_STATUS_KEY,
                ResourceWorkflowStep.STATUS_PENDING
            )
            if step_status != ResourceWorkflowStep.STATUS_COMPLETE:
                return idx, step

        # TODO: ALL STATUS COMPLETE OR NON READY - RETURN RESULTS OBJECT?
        return len(self.steps), self.steps[-1]

    def get_status(self):
        """
        Returns the status of the next workflow step.

        Returns:
            ResourceWorkflowStep.STATUS_X: status of the next step.
        """
        index, next_step = self.get_next_step()
        # TODO: Handle when next step is None or all complete...
        status = next_step.get_status(ResourceWorkflowStep.ROOT_STATUS_KEY)

        # If we are not on the first step and the status is pending, workflow status is continue
        if status == ResourceWorkflowStep.STATUS_PENDING and index > 0:
            return self.STATUS_CONTINUE

        return status
