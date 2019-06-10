"""
********************************************************************************
* Name: attributes_mixin.py
* Author: nswain
* Created On: April 23, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import json


class AttributesMixin(object):
    """
    Provides methods for implementing the attributes pattern.
    """
    _attributes = None

    @property
    def attributes(self):
        if not self._attributes:
            self._attributes = json.dumps({})
        return json.loads(self._attributes)

    @attributes.setter
    def attributes(self, value):
        self._attributes = json.dumps(value)

    def get_attribute(self, key):
        """
        Get value of a specific attribute.
        Args:
            key(str): key of attribute.

        Returns:
            varies: value of attribute.
        """
        if key not in self.attributes:
            return None

        return self.attributes[key]

    def set_attribute(self, key, value):
        """
        Set value of a specific attribute.
        Args:
            key(str): key of attribute
            value: value of attribute
        """
        attrs = self.attributes
        attrs[key] = value
        self.attributes = attrs

    @classmethod
    def build_attributes_string(cls, **kwargs):
        """
        Helper method that builds attributes string to use when querying.
        Args:
            **kwargs: any number of key value pairs to use for filtering.

        Returns:
            json: kwargs serialized into a json string.
        """
        attributes = cls.build_attributes(**kwargs)
        attributes_string = json.dumps(attributes)
        return attributes_string

    @classmethod
    def build_attributes(cls, **kwargs):
        """
        Helper method used to build attributes object.
        Args:
            **kwargs: any number of key value pairs to use for filtering.

        Returns:
            dict: kwargs serialized into dictionary.
        """
        from tethysext.atcore.models.app_users import AppUsersBase
        # Build attributes string for query
        attributes = {}
        for key in kwargs:
            if isinstance(kwargs[key], AppUsersBase):
                value = str(kwargs[key].id)
            else:
                value = kwargs[key]

            attributes.update({key: value})
        return attributes
