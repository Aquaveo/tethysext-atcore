"""
********************************************************************************
* Name: options_mixin.py
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import copy


class OptionsMixin(object):
    """
    Provides methods for implementing the options pattern.
    """
    _options = None

    @property
    def default_options(self):
        """
        Returns default options dictionary for the object.
        """
        return {}

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        if not isinstance(value, dict):
            raise ValueError('The options must be a dictionary: {}'.format(value))
        opts = self._merge_options(self.default_options, value)
        self._options = opts

    def _merge_options(self, left, right):
        """
        Merge right hand dictionary onto left hand dictionary recursively.

        Args:
            left(dict): baseline dictionary
            right(dict): overriding dictionary

        Returns:
            dict: The merged dictionary.
        """
        temp_right = copy.deepcopy(right)
        temp_left = copy.deepcopy(left)

        for k, v in temp_right.items():
            if isinstance(v, dict) and k in temp_left:
                if isinstance(temp_left[k], dict):
                    temp_right[k] = self._merge_options(temp_left[k], temp_right[k])

        temp_left.update(temp_right)
        return temp_left
