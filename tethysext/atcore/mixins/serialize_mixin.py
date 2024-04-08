import json

from tethysext.atcore.utilities import json_serializer


class SerializeMixin:
    def serialize_base_fields(self, d: dict) -> dict:
        """Hook for ATCore base classes to add their custom fields to serialization.

        Args:
            d: Base serialized Resource dictionary.

        Returns:
            Serialized Resource dictionary.
        """
        return d

    def serialize_custom_fields(self, d: dict):
        """Hook for app-specific subclasses to add additional fields to serialization.

        Args:
            base: Base serialized Resource dictionary.

        Returns:
            dict: Serialized Resource.
        """
        return d

    def serialize_resource_props(self) -> dict:
        """Serialize the normal Resource properties into a dictionary.

        Returns:
            Serialized Resource dictionary.
        """
        from tethysext.atcore.mixins import UserLockMixin, AttributesMixin, StatusMixin

        d = {
            'id': self.id,
            'date_created': self.date_created,
            'name': self.name,
            'type': self.type,
        }

        if isinstance(self, UserLockMixin):
            d.update({
                'locked': self.is_user_locked,
            })

        if isinstance(self, StatusMixin):
            d.update({
                'status': self.get_status(),
            })

        if isinstance(self, AttributesMixin):
            d.update({
                'attributes': self.attributes,
            })
        return d

    def json_dumps(self, d: dict) -> str:
        """Serialize this Resource to a json string.

        Returns:
            str: JSON string.
        """
        return json.dumps(d, default=json_serializer)

    def serialize(self, format: str = 'dict'):
        """Serialize this Resource.

        Args:
            format: Format to serialize to. One of 'dict' or 'json'.

        Returns:
            dict: Serialized Resource.
        """
        if format not in ['dict', 'json']:
            raise ValueError(f'Invalid format: "{format}". Must be one of "dict" or "json".')
        d = self.serialize_resource_props()
        d = self.serialize_base_fields(d)
        d = self.serialize_custom_fields(d)

        # Convert to json string if requested
        if format == 'json':
            return self.json_dumps(d)

        return d
