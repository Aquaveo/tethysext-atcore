import datetime
import json
from uuid import UUID


class SerializeMixin:
    def serialize_resource_props(self) -> dict:
        """Serialize the normal Resource properties into a dictionary.

        Returns:
            Serialized Resource dictionary.
        """
        return {
            'id': self.id,
            'attributes': self.attributes,
            'created_by': self.created_by,
            'date_created': self.date_created,
            'description': self.description,
            'display_type_plural': self.DISPLAY_TYPE_PLURAL,
            'display_type_singular': self.DISPLAY_TYPE_SINGULAR,
            'locked': self.is_user_locked,
            'name': self.name,
            'organizations': [{
                'id': org.id,
                'name': org.name
            } for org in self.organizations],
            'public': self.public,
            'slug': self.SLUG,
            'status': self.get_status(),
            'type': self.type,
        }

    def json_dumps(self, d: dict) -> str:
        """Serialize this Resource to a json string.

        Returns:
            str: JSON string.
        """
        def json_default(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, UUID):
                return str(obj)
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

        return json.dumps(d, default=json_default)
