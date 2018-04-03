import json


class StatusMixin(object):
    """
    Provides convenience methods for managing a status attribute.
    """
    # User Project Statuses
    STATUS_PENDING = 'Pending'
    STATUS_DELETING = 'Deleting'
    STATUS_AVAILABLE = 'Available'
    STATUS_FAILED = 'Failed'
    STATUS_NONE = 'None'
    STATUS_EMPTY = ''
    STATUS_RESET = 'Reset'
    STATUS_ERROR = 'Error'
    STATUS_DIRTY = 'Dirty'
    STATUS_SUCCESS = 'Success'
    STATUS_COMPLETE = 'Complete'

    # Default status dict
    status_template = dict()

    def __init__(self, *args, **kwargs):
        super(StatusMixin, self).__init__(*args, **kwargs)

    @classmethod
    def get_status_options_list(cls):
        return [cls.STATUS_AVAILABLE, cls.STATUS_PENDING, cls.STATUS_DELETING,
                cls.STATUS_EMPTY, cls.STATUS_ERROR, cls.STATUS_FAILED,
                cls.STATUS_RESET, cls.STATUS_NONE, cls.STATUS_SUCCESS,
                cls.STATUS_COMPLETE]

    def get_status(self, key, default=None):
        """
        Get status for a given value.
        """
        if self.status is None:
            status_dict = self.status_template

        else:
            status_dict = json.loads(self.status)

        try:
            status_result = status_dict[key]
        except KeyError:
            status_result = default

        return status_result

    def set_status(self, key, status):
        """
        Set status for given key.
        """
        if self.status is None:
            status_dict = self.status_template
        else:
            status_dict = json.loads(self.status)

        status_dict[key] = status
        status_str = json.dumps(status_dict)
        self.status = status_str
