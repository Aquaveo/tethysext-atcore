"""
********************************************************************************
* Name: options_mixin.py
* Author: nswain
* Created On: April 30, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""


class OptionsMixin(object):
    """
    Provides methods for implementing the options pattern.
    """
    _options = None

    @property
    def default_options(self):
        """
        Returns default options dictionary for the result.
        """
        return {}

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        if not isinstance(value, dict):
            raise ValueError('The options must be a dictionary: {}'.format(value))
        opts = self.default_options
        opts.update(value)
        self._options = opts
