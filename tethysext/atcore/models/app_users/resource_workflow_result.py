"""
********************************************************************************
* Name: resource_workflow_result
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import uuid

from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, ForeignKey, String, PickleType, Integer
from tethysext.atcore.models.types import GUID
from tethysext.atcore.mixins import StatusMixin, AttributesMixin, OptionsMixin
from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.controller_metadata import ControllerMetadata


__all__ = ['ResourceWorkflowResult']


class ResourceWorkflowResult(AppUsersBase, StatusMixin, AttributesMixin, OptionsMixin):
    """
    Data model for storing information about resource workflow results.
    """
    __tablename__ = 'app_users_resource_workflow_results'
    CONTROLLER = ''
    TYPE = 'generic_workflow_result'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    resource_workflow_id = Column(GUID, ForeignKey('app_users_resource_workflows.id'))
    controller_metadata_id = Column(GUID, ForeignKey('app_users_controller_metadata.id'))
    type = Column(String)
    name = Column(String)
    description = Column(String)
    order = Column(Integer)
    data = Column(PickleType, default={})
    _options = Column(PickleType, default={})
    _attributes = Column(String)
    _controller = relationship('ControllerMetadata', cascade="all,delete", uselist=False,
                               backref=backref('result'))

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'options' in kwargs:
            self.options = kwargs['options']
        else:
            self._options = self.default_options

    def __str__(self):
        return '<{} name="{}" id="{}" >'.format(self.__class__.__name__, self.name, self.id)

    @property
    def controller(self):
        if not self._controller:
            self._controller = ControllerMetadata(path=self.CONTROLLER)
        return self._controller
