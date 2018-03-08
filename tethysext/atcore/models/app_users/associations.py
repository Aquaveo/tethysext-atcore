from sqlalchemy import Column, Integer, Table, ForeignKey
from tethysext.atcore.models.types.guid import GUID

from .base import AppUsersBase

user_organization_association = Table(
    'user_organization_association',
    AppUsersBase.metadata,
    Column('id', Integer, primary_key=True),
    Column('app_user_id', GUID, ForeignKey('app_users.id')),
    Column('organization_id', GUID, ForeignKey('organizations.id'))
)

organization_resource_association = Table(
    'organization_resource_association',
    AppUsersBase.metadata,
    Column('id', Integer, primary_key=True),
    Column('resource_id', GUID, ForeignKey('resources.id')),
    Column('organization_id', GUID, ForeignKey('organizations.id'))
)
