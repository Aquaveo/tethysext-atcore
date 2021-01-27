import uuid

from sqlalchemy import Table, Column, ForeignKey

from tethysext.atcore.models.app_users.base import AppUsersBase
from tethysext.atcore.models.types import GUID

resource_file_collection_association = Table(
    'resource_file_collections_association',
    AppUsersBase.metadata,
    Column('id', GUID, primary_key=True, default=uuid.uuid4),
    Column('resource_id', GUID, ForeignKey('app_users_resources.id')),
    Column('file_collection_id', GUID, ForeignKey('file_collections.id'))
)
