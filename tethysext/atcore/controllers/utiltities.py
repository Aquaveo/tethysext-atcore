"""
********************************************************************************
* Name: utilities.py
* Author: glarsen, nswain
* Created On: December 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""


def get_style_for_status(status):
    """
    Return appropriate style for given status.

    Args:
        status(str): One of StatusMixin statuses.

    Returns:
        str: style for the given status.
    """
    from tethysext.atcore.mixins import StatusMixin

    if status in [StatusMixin.STATUS_COMPLETE, StatusMixin.STATUS_APPROVED, StatusMixin.STATUS_REVIEWED]:
        return 'success'

    elif status in [StatusMixin.STATUS_SUBMITTED, StatusMixin.STATUS_UNDER_REVIEW,
                    StatusMixin.STATUS_CHANGES_REQUESTED, StatusMixin.STATUS_WORKING]:
        return 'warning'

    elif status in [StatusMixin.STATUS_ERROR, StatusMixin.STATUS_FAILED, StatusMixin.STATUS_REJECTED]:
        return 'danger'

    return 'primary'
