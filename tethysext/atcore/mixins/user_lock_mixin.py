"""
********************************************************************************
* Name: user_lock_mixin.py
* Author: nswain
* Created On: September 24, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""


class UserLockMixin:
    """
    Provides methods for implementing the user lock pattern.
    """
    _user_lock = None
    LOCKED_FOR_ALL_USERS = '__locked_for_all_users__'

    def acquire_user_lock(self, request=None):
        """
        Acquire a user lock for the given request user. Only the given user will be able to access the workflow in read-write mode. All other users will have read-only access. If no user is provided, the workflow will be locked for all users.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if acquisition was successful. False if already locked.
        """  # noqa: E501
        lock_acquired = False
        already_locked = self.is_user_locked

        if request is None:
            if not already_locked:
                self._user_lock = self.LOCKED_FOR_ALL_USERS
                lock_acquired = True
            # if already locked and ...
            elif self.is_locked_for_all_users:
                lock_acquired = True

        else:  # request given
            if not already_locked:
                self._user_lock = request.user.username
                lock_acquired = True
            # if already locked and ...
            elif self.user_lock == request.user.username:
                lock_acquired = True

        return lock_acquired

    def release_user_lock(self, request):
        """
        Release the user lock for the request user user. Only the user that was used to acquire the lock or other user with appropriate permissions (e.g. admin or staff user) can release a user lock. If the workflow is locked for all users, an admin will be required to unlock it.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if release was successful or if the user lock was not locked. False otherwise.
        """  # noqa: E501
        from tethys_sdk.permissions import has_permission

        lock_released = False
        can_override = has_permission(request, 'can_override_user_locks')

        if not self.is_user_locked:
            # lock is already unlocked
            lock_released = True
        elif self.is_locked_for_all_users and can_override:
            # lock is locked for all uses and can only be unlocked by users with override permissions
            self._user_lock = None
            lock_released = True
        elif self.user_lock == request.user.username:
            # lock is locked for the given user
            self._user_lock = None
            lock_released = True
        elif can_override:
            # lock is locked, not for all users or the given user, but user has override permissions
            self._user_lock = None
            lock_released = True

        return lock_released

    def is_locked_for_request_user(self, request):
        """
        Determine if the lock is locked for the request user.

        Args:
            request(django.http.HttpRequest): The Django Request.

        Returns:
            bool: True if workflow is locked for request user.
        """
        from tethys_sdk.permissions import has_permission

        if has_permission(request, 'can_override_user_locks'):
            return False

        return self.is_user_locked and self._user_lock != request.user.username

    @property
    def user_lock(self):
        """
        Get the current value of the user lock.

        Returns:
            str or None: the username of the user that has read-write access, LOCKED_FOR_ALL_USERS if locked for all users, or None if the user lock is not locked.
        """  # noqa: E501
        return self._user_lock

    @property
    def is_user_locked(self):
        """
        Check if the workflow is user locked.

        Returns:
            bool: True if the workflow is user locked, False if not.
        """
        return self._user_lock is not None and self._user_lock != ''

    @property
    def is_locked_for_all_users(self):
        """
        Check if the workflow is user locked for all users.

        Returns:
            bool: True if the workflow is user locked for all users, False if not.
        """  # noqa: E501
        return self._user_lock == self.LOCKED_FOR_ALL_USERS
