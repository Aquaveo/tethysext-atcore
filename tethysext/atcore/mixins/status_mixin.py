import json


class StatusMixin(object):
    """
    Provides methods for implementing the status pattern.
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
    STATUS_CONTINUE = 'Continue'
    STATUS_UNDER_REVIEW = 'Under Review'
    STATUS_SUBMITTED = 'Submitted'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHANGES_REQUESTED = 'Changes Requested'

    OK_STATUSES = [STATUS_AVAILABLE, STATUS_SUCCESS, STATUS_COMPLETE, STATUS_OK, STATUS_CONTINUE, STATUS_APPROVED]
    ERROR_STATUSES = [STATUS_FAILED, STATUS_ERROR]
    WORKING_STATUSES = [STATUS_PROCESSING, STATUS_PENDING, STATUS_WAITING, STATUS_WORKING, STATUS_UNDER_REVIEW,
                        STATUS_SUBMITTED, STATUS_CHANGES_REQUESTED, STATUS_DIRTY]
    NULL_STATUSES = [STATUS_EMPTY, STATUS_NONE]

    ROOT_STATUS_KEY = 'root'

    status = None

    def __init__(self, *args, **kwargs):
        super(StatusMixin, self).__init__(*args, **kwargs)

    @classmethod
    def valid_statuses(cls):
        return [cls.STATUS_AVAILABLE, cls.STATUS_PENDING, cls.STATUS_DELETING,
                cls.STATUS_EMPTY, cls.STATUS_ERROR, cls.STATUS_FAILED,
                cls.STATUS_RESET, cls.STATUS_NONE, cls.STATUS_SUCCESS,
                cls.STATUS_COMPLETE, cls.STATUS_PROCESSING, cls.STATUS_WAITING,
                cls.STATUS_OK, cls.STATUS_WORKING, cls.STATUS_UNKNOWN,
                cls.STATUS_CONTINUE, cls.STATUS_UNDER_REVIEW, cls.STATUS_SUBMITTED,
                cls.STATUS_APPROVED, cls.STATUS_REJECTED, cls.STATUS_CHANGES_REQUESTED,
                cls.STATUS_DIRTY]

    def get_status(self, key=ROOT_STATUS_KEY, default=None):
        """
        Get status for a given value.
        """
        if self.status is None:
            status_dict = {}

        else:
            status_dict = json.loads(self.status)

        try:
            status_result = status_dict[key]

            if not status_result:
                status_result = default

        except KeyError:
            status_result = default

        return status_result

    def set_status(self, key=ROOT_STATUS_KEY, status=None):
        """
        Set status for given key.
        """
        if status not in self.valid_statuses() and status is not None:
            raise ValueError(f'"{status}" is not a valid status.')

        if self.status is None:
            status_dict = {}
        else:
            status_dict = json.loads(self.status)

        status_dict[key] = status
        status_str = json.dumps(status_dict)
        self.status = status_str
