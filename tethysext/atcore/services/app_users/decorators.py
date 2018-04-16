"""
********************************************************************************
* Name: decorators
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.functional import wraps


def active_user_required():
    def decorator(controller_func):
        def _wrapped_controller(self, request, *args, **kwargs):
            # Require logged in user (aka: not AnonymousUser)
            if not request.user or isinstance(request.user, AnonymousUser):
                # prompt login
                return redirect(reverse('accounts:login') + '?next=' + request.path)

            # Validate that the user is active.
            if not request.user.is_staff:
                _AppUser = self.get_app_user_model()
                make_session = self.get_sessionmaker()

                session = make_session()
                app_user = session.query(_AppUser).\
                    filter(_AppUser.username == request.user.username).\
                    one_or_none()
                session.close()

                if app_user is None:
                    messages.warning(request, "We're sorry, but you are not allowed access to this app.")
                    return redirect(reverse('app_library'))

                if not app_user.is_active:
                    messages.warning(request, "We're sorry, but your account has been disabled for this app. "
                                              "Please contact your organization's admin for further "
                                              "questions and assistance.")
                    return redirect(reverse('app_library'))

            return controller_func(self, request, *args, **kwargs)

        return wraps(controller_func)(_wrapped_controller)
    return decorator
