"""
********************************************************************************
* Name: decorators
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.functional import wraps


# TODO: Generalize to work with function and method controllers. If possible...
def active_user_required(*args, **kwargs):
    def decorator(controller_func):
        @login_required()
        def _wrapped_controller(request, *args, **kwargs):
            if not request.user.is_staff:
                from tethysapp.epanet.model import SessionMaker, AppUser
                session = SessionMaker()
                app_user = session.query(AppUser).filter(AppUser.username == request.user.username).one_or_none()
                session.close()
                if app_user is None:
                    messages.warning(request, "We're sorry, but you are not allowed access to this app.")
                    return redirect(reverse('app_library'))
                else:
                    if app_user.is_active is False:
                        messages.warning(request, "We're sorry, but your account has been disabled for this app. "
                                                  "Please contact your organization's admin for further "
                                                  "questions and assistance.")
                        return redirect(reverse('app_library'))
            return controller_func(request, *args, **kwargs)
        return wraps(controller_func)(_wrapped_controller)
    return decorator
