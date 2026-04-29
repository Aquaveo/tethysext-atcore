"""
********************************************************************************
* Name: resource_workflow_result
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, PickleType, Integer
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, OptionsMixin, SerializeMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.controller_metadata import ControllerMetadata

if TYPE_CHECKING:
    from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
    from tethysext.atcore.models.resource_workflow_steps.results_rws import ResultsResourceWorkflowStep


__all__ = ['ResourceWorkflowResult']


class ResourceWorkflowResult(AppUsersBase, StatusMixin, AttributesMixin, OptionsMixin, SerializeMixin):
    """
    Data model for storing information about resource workflow results.
    """
    __tablename__ = 'app_users_resource_workflow_results'
    CONTROLLER = 'tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView'
    TYPE = 'generic_workflow_result'

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    resource_workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey('app_users_resource_workflows.id'),
    )
    controller_metadata_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey('app_users_controller_metadata.id'),
    )
    type: Mapped[Optional[str]] = mapped_column(String)
    name: Mapped[Optional[str]] = mapped_column(String)
    codename: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    order: Mapped[Optional[int]] = mapped_column(Integer)
    _data: Mapped[Optional[dict]] = mapped_column(PickleType, default={})
    _options: Mapped[Optional[dict]] = mapped_column(PickleType, default={})
    _attributes: Mapped[Optional[str]] = mapped_column(String)

    _controller: Mapped[Optional["ControllerMetadata"]] = relationship(
        'ControllerMetadata',
        back_populates='result',
        cascade='all,delete',
        uselist=False,
    )

    workflow: Mapped[Optional["ResourceWorkflow"]] = relationship(
        'ResourceWorkflow',
        back_populates='results',
    )

    steps: Mapped[list["ResultsResourceWorkflowStep"]] = relationship(
        'ResultsResourceWorkflowStep',
        secondary='app_users_step_result_association',
        back_populates='results',
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        controller = kwargs.pop('controller', self.CONTROLLER)
        super().__init__(*args, **kwargs)

        if 'options' in kwargs:
            self.options = kwargs['options']
        else:
            self._options = self.default_options

        self._controller = ControllerMetadata(path=controller)

    def __str__(self):
        return '<{} name="{}" id="{}" >'.format(self.__class__.__name__, self.name, self.id)

    def __repr__(self):
        return self.__str__()

    @property
    def controller(self):
        return self._controller

    @property
    def data(self):
        if not self._data:
            self._data = dict()
        return self._data

    @data.setter
    def data(self, value):
        self._data = dict()
        session = Session.object_session(self)
        session and session.commit()
        self._data = value
        session and session.commit()

    def reset(self):
        """
        Resets result to initial state.
        """
        self._data = dict()

    def serialize_base_fields(self, d: dict) -> dict:
        """Hook for ATCore base classes to add their custom fields to serialization.

        Args:
            d: Base serialized Resource dictionary.

        Returns:
            Serialized Resource dictionary.
        """
        d.update({
            'codename': self.codename,
            'data': self.data,
            'order': self.order,
        })
        return d
