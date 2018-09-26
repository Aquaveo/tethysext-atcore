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
from tethysext.atcore.mixins import StatusMixin, AttributesMixin
from tethysext.atcore.models.app_users.base import AppUsersBase


__all__ = ['ResourceWorkflow']


class ResourceWorkflow(AppUsersBase, StatusMixin, AttributesMixin):
    """
    Data model for storing information about resource workflows.
    """
    __tablename__ = 'app_users_resource_workflows'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    resource_id = Column(GUID, ForeignKey('app_users_resources.id'))
    creator_id = Column(GUID, ForeignKey('app_users_app_users.id'))

    name = Column(String)
    type = Column(String)
    date_created = Column(DateTime, default=dt.datetime.utcnow)
    status = Column(String)
    _attributes = Column(String)

    resource = relationship('Resource', backref='workflows')
    creator = relationship('AppUser', backref='workflows')

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic_workflow'
    }
