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
    STATUS_PROCESSING = 'Processing'
    STATUS_WAITING = 'Waiting'
    STATUS_OK = 'OK'
    STATUS_WORKING = 'Working'
    STATUS_UNKNOWN = 'Unknown'

    OK_STATUSES = [STATUS_AVAILABLE, STATUS_SUCCESS, STATUS_COMPLETE, STATUS_OK]
    ERROR_STATUSES = [STATUS_FAILED, STATUS_ERROR]
    WORKING_STATUSES = [STATUS_PROCESSING, STATUS_PENDING, STATUS_WAITING, STATUS_WORKING]
    NULL_STATUSES = [STATUS_EMPTY, STATUS_NONE]

    ROOT_STATUS_KEY = 'root'

    # Default status dict
    status_template = dict()

    def __init__(self, *args, **kwargs):
        super(StatusMixin, self).__init__(*args, **kwargs)

    @classmethod
    def get_status_options_list(cls):
        return [cls.STATUS_AVAILABLE, cls.STATUS_PENDING, cls.STATUS_DELETING,
                cls.STATUS_EMPTY, cls.STATUS_ERROR, cls.STATUS_FAILED,
                cls.STATUS_RESET, cls.STATUS_NONE, cls.STATUS_SUCCESS,
                cls.STATUS_COMPLETE, cls.STATUS_PROCESSING, cls.STATUS_WAITING,
                cls.STATUS_OK, cls.STATUS_WORKING, cls.STATUS_UNKNOWN]

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
