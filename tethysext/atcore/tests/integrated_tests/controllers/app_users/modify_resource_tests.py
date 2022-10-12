"""
********************************************************************************
* Name: modify_resource_tests.py
* Author: mlebaron
* Created On: October 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from django.http import QueryDict
from django.contrib.auth.models import User
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.controllers.app_users.modify_resource import ModifyResource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ModifyResourceTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'

        )
        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.user = staff_user
        self.request.FILES = []
        self.request.POST = QueryDict('', mutable=True)
        self.request.POST.update({
            'modify-resource-submit': True,
            'resource-name': 'Resource',
            'resource-description': 'resource_description',
            'assign-organizations': ['Aquaveo']
        })

        self.resource = Resource()
        self.session.add(self.resource)
        self.session.commit()

        app_user_model_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_app_user_model')  # noqa: E501
        self.get_app_user_model = app_user_model_patcher.start()
        self.get_app_user_model.return_value = mock.MagicMock()
        self.addCleanup(app_user_model_patcher.stop)

        get_organization_model_patcher = mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_organization_model')  # noqa: E501
        self.get_organization_model = get_organization_model_patcher.start()
        self.get_organization_model.return_value = mock.MagicMock()
        self.addCleanup(get_organization_model_patcher.stop)

        get_resource_model_patcher = mock.patch.object(AppUsersViewMixin, 'get_resource_model')
        self.get_resource_model = get_resource_model_patcher.start()
        self.get_resource_model.return_value = mock.MagicMock()
        self.addCleanup(get_resource_model_patcher.stop)

        get_sessionmaker_patcher = mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
        self.get_sessionmaker = get_sessionmaker_patcher.start()
        self.get_sessionmaker.return_value = mock.MagicMock()
        self.addCleanup(get_sessionmaker_patcher.stop)

        has_permission_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.has_permission')
        self.has_permission = has_permission_patcher.start()
        self.has_permission.return_value = True
        self.addCleanup(has_permission_patcher.stop)

        has_permission_decorator_patcher = mock.patch('tethys_apps.decorators.has_permission')
        self.has_permission_decorator = has_permission_decorator_patcher.start()
        self.has_permission_decorator.return_value = True
        self.addCleanup(has_permission_decorator_patcher.stop)

        get_active_app_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.get_active_app')  # noqa: E501
        self.get_active_app = get_active_app_patcher.start()
        self.get_active_app.return_value = mock.MagicMock(url_namespace='app_namespace')
        self.addCleanup(get_active_app_patcher.stop)

        log_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.log')
        self.mock_log = log_patcher.start()
        self.addCleanup(log_patcher.stop)

        massages_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.messages')
        self.mock_messages = massages_patcher.start()
        self.addCleanup(massages_patcher.stop)

        reverse_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.reverse')
        self.mock_reverse = reverse_patcher.start()
        self.addCleanup(reverse_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.redirect')
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        render_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_resource.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

    def tearDown(self):
        super().tearDown()

    @mock.patch.object(ModifyResource, '_handle_modify_resource_requests')
    def test_get(self, mock_handle):
        mock_handle.return_value = {'success': True}
        controller = ModifyResource.as_controller()
        self.request.method = 'get'

        ret = controller(self.request)

        self.assertTrue(ret['success'])

    @mock.patch.object(ModifyResource, '_handle_modify_resource_requests')
    def test_post(self, mock_handle):
        mock_handle.return_value = {'success': True}
        controller = ModifyResource.as_controller()
        self.request.method = 'post'

        ret = controller(self.request)

        self.assertTrue(ret['success'])

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_without_resource_id(self, _):
        self.request.FILES = []
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST = QueryDict('', mutable=True)
        self.request.POST.update({
            'modify-resource-submit': True,
            'resource-name': 'Resource',
            'resource-description': 'resource_description',
            'assign-organizations': ['Aquaveo']
        })
        modify_resource = ModifyResource()
        modify_resource.include_file_upload = True

        modify_resource._handle_modify_resource_requests(self.request)

        self.assertTrue(self.mock_redirect.called)
        self.assertTrue(self.mock_reverse.called)

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_editing(self, _):
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST.pop('resource-name')
        modify_resource = ModifyResource()
        modify_resource.include_srid = True

        modify_resource._handle_modify_resource_requests(self.request, resource_id=self.resource.id)

        self.assertTrue(self.mock_render.called)
        self.assertTrue(self.mock_reverse.called)

    @mock.patch.object(ModifyResource, 'can_edit_resource')
    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_cannot_edit_resource(self, _, mock_can_edit_resource):
        mock_can_edit_resource.return_value = False, 'Error message'
        self.request.FILES = []
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST.pop('assign-organizations')

        ModifyResource()._handle_modify_resource_requests(self.request, resource_id=self.resource.id)

        msg_args = self.mock_messages.error.call_args_list
        self.assertEqual('Error message', msg_args[0][0][1])
        self.assertEqual('Error message', self.mock_log.exception.call_args_list[0][0][0])

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_include_srid(self, _):
        self.request.GET = {'next': 'manage-organizations'}
        modify_resource = ModifyResource()
        modify_resource.include_srid = True

        modify_resource._handle_modify_resource_requests(self.request, resource_id=self.resource.id)

        self.assertTrue(self.mock_redirect.called)
        self.assertTrue(self.mock_reverse.called)

    def test_handle_modify_resource_requests_with_resource_id(self):
        self.request.GET = {'next': ''}

        ModifyResource()._handle_modify_resource_requests(self.request, resource_id=self.resource.id)

        self.assertTrue(self.mock_redirect.called)
        self.assertTrue(self.mock_reverse.called)

    def test_handle_modify_resource_requests_atcore_exception(self):
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST = {'modify-resource-submit': True}
        self.has_permission.return_value = False

        ModifyResource()._handle_modify_resource_requests(self.request)

        msg_args = self.mock_messages.error.call_args_list
        self.assertIn("We're sorry, but you are not able to create", msg_args[0][0][1])
        self.assertIn("We're sorry, but you are not able to create", self.mock_log.exception.call_args_list[0][0][0])

    def test_handle_modify_resource_requests_no_organizations(self):
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST.pop('assign-organizations')

        ModifyResource()._handle_modify_resource_requests(self.request)

        self.assertTrue(self.mock_render.called)
        self.assertTrue(self.mock_reverse.called)

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_no_resource_name(self, _):
        self.request.GET = {'next': 'manage-organizations'}
        self.request.POST.pop('resource-name')
        modify_resource = ModifyResource()
        modify_resource.include_file_upload = True

        modify_resource._handle_modify_resource_requests(self.request)

        self.assertTrue(self.mock_render.called)
        self.assertTrue(self.mock_reverse.called)

    @mock.patch('traceback.print_exc')
    @mock.patch.object(ModifyResource, 'can_create_resource')
    def test_handle_modify_resource_requests_non_atcore_exception(self, mock_can_create, mock_print_exe):
        mock_can_create.raiseError.side_effect = mock.MagicMock(side_effect=Exception('Generic Exception error'))
        self.request.GET = {'next': 'manage-organizations'}

        ModifyResource()._handle_modify_resource_requests(self.request)

        self.assertTrue(mock_print_exe.called)
        msg_args = self.mock_messages.error.call_args_list
        self.assertEqual('An unexpected error occurred while uploading your project. Please try again or contact '
                         'support@aquaveo.com for further assistance.', msg_args[0][0][1])
        self.assertEqual('An unexpected error occurred while uploading your project. Please try again or contact '
                         'support@aquaveo.com for further assistance.', self.mock_log.exception.call_args_list[0][0][0])

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_upload_error(self, _):
        self.request.GET = {'next': 'manage-organizations'}
        modify_resource = ModifyResource()
        modify_resource.include_file_upload = True
        modify_resource.file_upload_required = True

        modify_resource._handle_modify_resource_requests(self.request)

        self.assertTrue(self.mock_render.called)
        self.assertTrue(self.mock_reverse.called)

    @mock.patch.object(ModifyResource, 'handle_file_upload')
    def test_handle_modify_resource_requests_resource_srid_error(self, _):
        self.request.GET = {'next': 'manage-organizations'}
        modify_resource = ModifyResource()
        modify_resource.include_srid = True
        modify_resource.srid_required = True

        modify_resource._handle_modify_resource_requests(self.request)

        self.assertTrue(self.mock_render.called)
        self.assertTrue(self.mock_reverse.called)

    def test_can_create_resource(self):
        permission, error_msg = ModifyResource().can_create_resource(self.session, self.request, mock.MagicMock())

        self.assertTrue(permission)
        self.assertIn("We're sorry, but you are not able to create", error_msg)

    def test_can_edit_resource(self):
        permission, error_msg = ModifyResource().can_edit_resource(self.session, self.request,
                                                                   mock.MagicMock(), self.resource)

        self.assertTrue(permission)
        self.assertIn("We're sorry, but you are not allowed to edit this", error_msg)

    def test_handle_srid_changed(self):
        ModifyResource().handle_srid_changed(self.session, self.request, mock.MagicMock(),
                                             self.resource, '1234', '4321')

    def test_handle_resource_finished_processing(self):
        ModifyResource().handle_resource_finished_processing(self.session, self.request, mock.MagicMock(),
                                                             self.resource, True)

    def test_get_context(self):
        context = {'success': True}

        ret_context = ModifyResource().get_context(request=self.request, context=context, editing=False)

        self.assertEqual(ret_context, context)
