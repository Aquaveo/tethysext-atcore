"""
********************************************************************************
* Name: decorators
* Author: nswain
* Created On: April 09, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import logging
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.functional import wraps
from django.conf import settings
from tethysext.atcore.exceptions import ATCoreException


log = logging.getLogger(__name__)


def active_user_required():
    def decorator(controller_func):
        def _wrapped_controller(self, request, *args, **kwargs):
            # Require logged in user (aka: not AnonymousUser)
            if (not request.user and not getattr(settings, 'ENABLE_OPEN_PORTAL', False)) or \
                    (not getattr(settings, 'ENABLE_OPEN_PORTAL', False) and isinstance(request.user, AnonymousUser)):
                # prompt login
                return redirect(reverse('accounts:login') + '?next=' + request.path)

            if getattr(settings, 'ENABLE_OPEN_PORTAL', False):
                return controller_func(self, request, *args, **kwargs)

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


def resource_controller(is_rest_controller=False):
    def decorator(controller_func):
        def _wrapped_controller(self, request, resource_id=None, back_url=None, *args, **kwargs):
            _Resource = self.get_resource_model()
            session = None
            resource = None

            try:
                make_session = self.get_sessionmaker()
                session = make_session()

                if resource_id:
                    resource = self.get_resource(request, resource_id=resource_id, session=session)

                # Call the Controller
                return controller_func(self, request, session, resource, back_url, *args, **kwargs)

            except (StatementError, NoResultFound) as e:
                message = 'The {} could not be found.'.format(
                    _Resource.DISPLAY_TYPE_SINGULAR.lower()
                )
                log.exception(message)
                messages.warning(request, message)
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except ATCoreException as e:
                error_message = str(e)
                messages.warning(request, error_message)
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except ValueError as e:
                if session:
                    session.rollback()
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            except RuntimeError as e:
                if session:
                    session.rollback()

                log.exception(str(e))
                messages.error(request, "We're sorry, an unexpected error has occurred.")
                if not is_rest_controller:
                    return redirect(self.back_url)
                else:
                    return JsonResponse({'success': False, 'error': str(e)})

            finally:
                session and session.close()

        return wraps(controller_func)(_wrapped_controller)
    return decorator
