"""
********************************************************************************
* Name: modify_organization_tests.py
* Author: mlebaron
* Created On: October 10, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest, QueryDict
from django.contrib.auth.models import User
from tethysext.atcore.controllers.app_users.mixins import AppUsersViewMixin, ResourceBackUrlViewMixin
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.controllers.app_users.modify_organization import ModifyOrganization
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class CustomModifyOrganization(ModifyOrganization):
    _Resources = [
        mock.MagicMock(
            SLUG='foos',
            DISPLAY_TYPE_PLURAL='Foos'
        ),
        mock.MagicMock(
            SLUG='bars',
            DISPLAY_TYPE_PLURAL='Bars'
        ),
    ]


class ModifyOrganizationsTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.resource1 = mock.MagicMock(
            SLUG='foos'
        )
        self.resource1.id = '12345'
        self.resource1.name = 'Foo Resource'
        self.resource2 = mock.MagicMock(
            SLUG='bars'
        )
        self.resource2.id = '67890'
        self.resource2.name = 'Bar Resource'

        self.organization = mock.MagicMock(
            name='Aquaveo',
            license='consultant',
            consultant=mock.MagicMock(id=11111),
            active=True,
            resources=[
                self.resource1,
                self.resource2,
            ]
        )

        self.user = UserFactory()
        self.app_user = mock.MagicMock(
            username=self.user.username,
            role=AppUser.ROLES.ORG_USER,
            is_active=True,
            one=mock.MagicMock()
        )
        self.app_user.one.return_value = self.organization

        self.staff_user = User.objects.create_superuser(
            username='foo',
            email='foo@bar.com',
            password='pass'
        )

        self.request = mock.MagicMock(spec=HttpRequest)
        self.request.user = self.user
        self.request.POST = QueryDict('', mutable=True)
        self.request.POST.update({})

        session_patcher = mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
        self.mock_session_maker = session_patcher.start()
        self.mock_session_maker.return_value = mock.MagicMock()
        self.addCleanup(session_patcher.stop)

        decorator_permission_patcher = mock.patch('tethys_apps.decorators.has_permission')
        self.mock_decorator_permission_patcher = decorator_permission_patcher.start()
        self.mock_decorator_permission_patcher.return_value = True
        self.addCleanup(decorator_permission_patcher.stop)

        organization_permission_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.has_permission')  # noqa: E501
        self.mock_organization_has_permission = organization_permission_patcher.start()
        self.mock_organization_has_permission.return_value = True
        self.addCleanup(organization_permission_patcher.stop)

        active_app_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.get_active_app')
        self.mock_get_active_app = active_app_patcher.start()
        self.mock_get_active_app.return_value = mock.MagicMock(url_namespace='app_namespace')
        self.addCleanup(active_app_patcher.stop)

        render_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        redirect_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.redirect')
        self.mock_redirect = redirect_patcher.start()
        self.addCleanup(redirect_patcher.stop)

        reverse_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.reverse')
        self.mock_reverse = reverse_patcher.start()
        self.addCleanup(reverse_patcher.stop)

        messages_patcher = mock.patch('tethysext.atcore.controllers.app_users.modify_organization.messages')
        self.mock_messages = messages_patcher.start()
        self.addCleanup(messages_patcher.stop)

        is_valid_patcher = mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.is_valid')
        self.mock_is_valid = is_valid_patcher.start()
        self.mock_is_valid.return_value = True
        self.addCleanup(is_valid_patcher.stop)

    def tearDown(self):
        super().tearDown()

    @mock.patch.object(ResourceBackUrlViewMixin, 'default_back_url', return_value='/some/back/url/')  # noqa:E501
    @mock.patch.object(ModifyOrganization, '_handle_modify_user_requests')  # noqa: E501
    def test_get(self, mock_handle, _):
        self.request.method = 'get'
        controller = CustomModifyOrganization.as_controller()

        controller(self.request)

        mock_handle.assert_called()

    @mock.patch.object(ResourceBackUrlViewMixin, 'default_back_url', return_value='/some/back/url/')  # noqa:E501
    @mock.patch.object(ModifyOrganization, '_handle_modify_user_requests')  # noqa: E501
    def test_post(self, mock_handle, _):
        self.request.method = 'post'
        controller = CustomModifyOrganization.as_controller()

        controller(self.request)

        mock_handle.assert_called()

    @mock.patch('tethysext.atcore.models.app_users.organization.Organization.can_add_client_with_license')
    @mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.must_have_consultant')
    @mock.patch.object(AppUsersViewMixin, 'get_sessionmaker')
    def test_get_license_to_consultant_map(self, mock_get_sessionmaker, mock_must_have_consultant,
                                           mock_can_add_client_with_license):
        mock_get_sessionmaker.return_value = mock.MagicMock()
        mock_must_have_consultant.return_value = True
        mock_can_add_client_with_license.return_value = True
        license_options = [('Standard', 'standard')]
        org = mock.MagicMock(spec=Organization, id=123456)
        organizations = [org]

        licenses = CustomModifyOrganization().get_license_to_consultant_map(self.request, license_options,
                                                                            organizations)

        self.assertEqual(['123456'], licenses['standard'])

    @mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.list')
    def test_get_hide_consultant_licenses(self, mock_list):
        mock_list.return_value = ('standard', 'advanced', 'garbage', 'professional', 'consultant')
        modify_organization = CustomModifyOrganization()

        licenses = modify_organization.get_hide_consultant_licenses(self.request)

        self.assertEqual(['garbage', 'consultant'], licenses)

    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_handle_modify_user_requests_valid_not_editing(self, mock_mixin_permissions):
        self.request.GET = {'next': 'manage-users'}
        self.request.POST.update({
            'organization-name': 'Aquaveo',
            'organization-resources': ['Resource'],
            'organization-consultant': 'consultant',
            'organization-license': 'standard',
            'modify-organization-submit': True
        })
        mock_mixin_permissions.return_value = True

        CustomModifyOrganization()._handle_modify_user_requests(self.request)

    def test_handle_modify_user_requests_new_organization(self):
        self.request.GET = {'next': 'manage-users'}

        CustomModifyOrganization()._handle_modify_user_requests(self.request)

        self.mock_render.assert_called()
        self.assertEqual(self.request, self.mock_render.call_args[0][0])
        self.assertEqual('atcore/app_users/modify_organization.html', self.mock_render.call_args[0][1])

        context = self.mock_render.call_args[0][2]

        self.assertEqual('Organization', context['page_title'])
        self.assertFalse(context['editing'])
        self.assertFalse(context['am_member'])

        self.assertEqual({}, context['organization_name_input']['attributes'])
        self.assertEqual('', context['organization_name_input']['classes'])
        self.assertEqual('organization-name', context['organization_name_input']['name'])
        self.assertEqual('Name', context['organization_name_input']['display_text'])
        self.assertEqual('', context['organization_name_input']['initial'])
        self.assertEqual('', context['organization_name_input']['placeholder'])
        self.assertEqual('', context['organization_name_input']['prepend'])
        self.assertEqual('', context['organization_name_input']['append'])
        self.assertEqual('', context['organization_name_input']['icon_prepend'])
        self.assertEqual('', context['organization_name_input']['icon_append'])
        self.assertFalse(context['organization_name_input']['disabled'])
        self.assertEqual('', context['organization_name_input']['error'])

        self.assertEqual({}, context['organization_type_select']['attributes'])
        self.assertEqual('', context['organization_type_select']['classes'])
        self.assertEqual('organization-license', context['organization_type_select']['name'])
        self.assertEqual('License', context['organization_type_select']['display_text'])
        self.assertTrue(context['organization_type_select']['initial_is_iterable'])
        self.assertEqual([], context['organization_type_select']['initial'])
        self.assertFalse(context['organization_type_select']['multiple'])
        self.assertFalse(context['organization_type_select']['original'])
        self.assertFalse(context['organization_type_select']['placeholder'])
        self.assertEqual('null', context['organization_type_select']['select2_options'])
        self.assertEqual([('Standard', 'standard'), ('Advanced', 'advanced'), ('Professional', 'professional'),
                         ('Consultant', 'consultant')], context['organization_type_select']['options'])
        self.assertFalse(context['organization_type_select']['disabled'])
        self.assertEqual('', context['organization_type_select']['error'])

        self.assertEqual({}, context['owner_select']['attributes'])
        self.assertEqual('', context['owner_select']['classes'])
        self.assertEqual('Consultant', context['owner_select']['display_text'])
        self.assertEqual('organization-consultant', context['owner_select']['name'])
        self.assertTrue(context['owner_select']['initial_is_iterable'])
        self.assertEqual([], context['owner_select']['initial'])
        self.assertFalse(context['owner_select']['multiple'])
        self.assertFalse(context['owner_select']['original'])
        self.assertFalse(context['owner_select']['placeholder'])
        self.assertEqual('null', context['owner_select']['select2_options'])
        self.assertIn('options', context['owner_select'])
        self.assertFalse(context['owner_select']['disabled'])
        self.assertEqual('', context['owner_select']['error'])

        self.assertEqual(2, len(context['resources_select_inputs']))
        self.assertEqual({}, context['resources_select_inputs'][0]['attributes'])
        self.assertEqual('', context['resources_select_inputs'][0]['classes'])
        self.assertEqual('Foos (Optional)', context['resources_select_inputs'][0]['display_text'])
        self.assertEqual('organization-resources-foos', context['resources_select_inputs'][0]['name'])
        self.assertTrue(context['resources_select_inputs'][0]['initial_is_iterable'])
        self.assertEqual([], context['resources_select_inputs'][0]['initial'])
        self.assertTrue(context['resources_select_inputs'][0]['multiple'])
        self.assertFalse(context['resources_select_inputs'][0]['original'])
        self.assertFalse(context['resources_select_inputs'][0]['placeholder'])
        self.assertEqual('null', context['resources_select_inputs'][0]['select2_options'])
        self.assertEqual([], context['resources_select_inputs'][0]['options'])
        self.assertFalse(context['resources_select_inputs'][0]['disabled'])
        self.assertEqual('', context['resources_select_inputs'][0]['error'])

        self.assertEqual({}, context['resources_select_inputs'][1]['attributes'])
        self.assertEqual('', context['resources_select_inputs'][1]['classes'])
        self.assertEqual('Bars (Optional)', context['resources_select_inputs'][1]['display_text'])
        self.assertEqual('organization-resources-bars', context['resources_select_inputs'][1]['name'])
        self.assertTrue(context['resources_select_inputs'][1]['initial_is_iterable'])
        self.assertEqual([], context['resources_select_inputs'][1]['initial'])
        self.assertTrue(context['resources_select_inputs'][1]['multiple'])
        self.assertFalse(context['resources_select_inputs'][1]['original'])
        self.assertFalse(context['resources_select_inputs'][1]['placeholder'])
        self.assertEqual('null', context['resources_select_inputs'][1]['select2_options'])
        self.assertEqual([], context['resources_select_inputs'][1]['options'])
        self.assertFalse(context['resources_select_inputs'][1]['disabled'])
        self.assertEqual('', context['resources_select_inputs'][1]['error'])

        self.assertEqual('app_namespace:app_users_manage_users', context['next_controller'])

        self.assertEqual({'standard': [''], 'advanced': [''], 'professional': [''], 'consultant': ['']},
                         context['license_to_consultant_map'])

        self.assertEqual('consultant', context['hide_consultant_licenses'][0])

        self.assertEqual({}, context['organization_status_toggle']['attributes'])
        self.assertEqual('', context['organization_status_toggle']['classes'])
        self.assertEqual('organization-status', context['organization_status_toggle']['name'])
        self.assertEqual('Status', context['organization_status_toggle']['display_text'])
        self.assertEqual('Active', context['organization_status_toggle']['on_label'])
        self.assertEqual('Inactive', context['organization_status_toggle']['off_label'])
        self.assertEqual('primary', context['organization_status_toggle']['on_style'])
        self.assertEqual('default', context['organization_status_toggle']['off_style'])
        self.assertEqual('medium', context['organization_status_toggle']['size'])
        self.assertTrue(context['organization_status_toggle']['initial'])
        self.assertFalse(context['organization_status_toggle']['disabled'])
        self.assertEqual('', context['organization_status_toggle']['error'])

    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_handle_modify_user_requests_modify_organization(self, _):
        self.request.GET = {'next': 'manage-resources-resources'}
        self.request.POST.update({
            'organization-name': 'Aquaveo',
            'organization-resources': ['Resource'],
            'organization-consultant': 'consultant',
            'organization-license': 'standard',
            'modify-organization-submit': True
        })
        self.organization.is_member.return_value = True

        CustomModifyOrganization()._handle_modify_user_requests(self.request, '123456')

        self.mock_redirect.assert_called()
        self.mock_reverse.assert_called()
        self.assertEqual('app_namespace:resources_manage_resources', self.mock_reverse.call_args[0][0])

    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_handle_modify_user_requests_invalid_modify_2(self, _):
        self.mock_organization_has_permission.return_value = False
        self.request.GET = {'next': 'manage-organizations-resources'}
        self.request.POST.update({
            'organization-consultant': 'consultant',
            'organization-resources': ['Resource'],
            'modify-organization-submit': True
        })
        self.organization.is_member.return_value = True

        CustomModifyOrganization()._handle_modify_user_requests(self.request, '123456')

    @mock.patch('tethysext.atcore.services.app_users.licenses.Licenses.must_have_consultant')
    @mock.patch('tethysext.atcore.models.app_users.app_user.AppUser.get_app_user_from_request')
    @mock.patch.object(AppUsersViewMixin, 'get_permissions_manager')
    def test_handle_modify_user_requests_invalid_modify(self, _, mock_get_app_user, mock_have_consultant):
        self.mock_organization_has_permission.return_value = False
        mock_have_consultant.return_value = True
        self.request.GET = {'next': 'manage-resources-resources'}
        self.request.POST.update({
            'organization-resources-foos': ['Baz'],
            'modify-organization-submit': True
        })
        app_user = mock.MagicMock(clients=[mock.MagicMock()], members=[mock.MagicMock()])
        x = mock.MagicMock()
        x.get_app_user_from_request.return_value = app_user
        x.is_staff.return_value = False
        mock_get_app_user.return_value = x

        CustomModifyOrganization()._handle_modify_user_requests(self.request, '123456')

        self.mock_render.assert_called()
        self.assertEqual(self.request, self.mock_render.call_args[0][0])
        self.assertEqual('atcore/app_users/modify_organization.html', self.mock_render.call_args[0][1])

        context = self.mock_render.call_args[0][2]

        self.assertEqual('Organization', context['page_title'])
        self.assertTrue(context['editing'])
        self.assertIn('am_member', context)

        self.assertEqual({}, context['organization_name_input']['attributes'])
        self.assertEqual('', context['organization_name_input']['classes'])
        self.assertEqual('organization-name', context['organization_name_input']['name'])
        self.assertEqual('Name', context['organization_name_input']['display_text'])
        self.assertEqual('', context['organization_name_input']['initial'])
        self.assertEqual('', context['organization_name_input']['placeholder'])
        self.assertEqual('', context['organization_name_input']['prepend'])
        self.assertEqual('', context['organization_name_input']['append'])
        self.assertEqual('', context['organization_name_input']['icon_prepend'])
        self.assertEqual('', context['organization_name_input']['icon_append'])
        self.assertFalse(context['organization_name_input']['disabled'])
        self.assertEqual('Name is required.', context['organization_name_input']['error'])

        self.assertEqual({}, context['organization_type_select']['attributes'])
        self.assertEqual('', context['organization_type_select']['classes'])
        self.assertEqual('organization-license', context['organization_type_select']['name'])
        self.assertEqual('License', context['organization_type_select']['display_text'])
        self.assertTrue(context['organization_type_select']['initial_is_iterable'])
        self.assertEqual([], context['organization_type_select']['initial'])
        self.assertFalse(context['organization_type_select']['multiple'])
        self.assertFalse(context['organization_type_select']['original'])
        self.assertFalse(context['organization_type_select']['placeholder'])
        self.assertEqual('null', context['organization_type_select']['select2_options'])
        self.assertFalse(context['organization_type_select']['disabled'])
        self.assertEqual('You do not have permission to assign this license to this organization.',
                         context['organization_type_select']['error'])

        self.assertEqual({}, context['owner_select']['attributes'])
        self.assertEqual('', context['owner_select']['classes'])
        self.assertEqual('Consultant', context['owner_select']['display_text'])
        self.assertEqual('organization-consultant', context['owner_select']['name'])
        self.assertTrue(context['owner_select']['initial_is_iterable'])
        self.assertEqual([], context['owner_select']['initial'])
        self.assertFalse(context['owner_select']['multiple'])
        self.assertFalse(context['owner_select']['original'])
        self.assertFalse(context['owner_select']['placeholder'])
        self.assertEqual('null', context['owner_select']['select2_options'])
        self.assertIn('options', context['owner_select'])
        self.assertFalse(context['owner_select']['disabled'])
        self.assertEqual('You must assign the organization to at least one consultant organization.',
                         context['owner_select']['error'])

        self.assertEqual(2, len(context['resources_select_inputs']))
        self.assertEqual({}, context['resources_select_inputs'][0]['attributes'])
        self.assertEqual('', context['resources_select_inputs'][0]['classes'])
        self.assertEqual('Foos (Optional)', context['resources_select_inputs'][0]['display_text'])
        self.assertEqual('organization-resources-foos', context['resources_select_inputs'][0]['name'])
        self.assertTrue(context['resources_select_inputs'][0]['initial_is_iterable'])
        self.assertEqual([['Baz']], context['resources_select_inputs'][0]['initial'])
        self.assertTrue(context['resources_select_inputs'][0]['multiple'])
        self.assertFalse(context['resources_select_inputs'][0]['original'])
        self.assertFalse(context['resources_select_inputs'][0]['placeholder'])
        self.assertEqual('null', context['resources_select_inputs'][0]['select2_options'])
        self.assertEqual([], context['resources_select_inputs'][0]['options'])
        self.assertFalse(context['resources_select_inputs'][0]['disabled'])
        self.assertEqual('', context['resources_select_inputs'][0]['error'])

        self.assertEqual({}, context['resources_select_inputs'][1]['attributes'])
        self.assertEqual('', context['resources_select_inputs'][1]['classes'])
        self.assertEqual('Bars (Optional)', context['resources_select_inputs'][1]['display_text'])
        self.assertEqual('organization-resources-bars', context['resources_select_inputs'][1]['name'])
        self.assertTrue(context['resources_select_inputs'][1]['initial_is_iterable'])
        self.assertEqual([], context['resources_select_inputs'][1]['initial'])
        self.assertTrue(context['resources_select_inputs'][1]['multiple'])
        self.assertFalse(context['resources_select_inputs'][1]['original'])
        self.assertFalse(context['resources_select_inputs'][1]['placeholder'])
        self.assertEqual('null', context['resources_select_inputs'][1]['select2_options'])
        self.assertEqual([], context['resources_select_inputs'][1]['options'])
        self.assertFalse(context['resources_select_inputs'][1]['disabled'])
        self.assertEqual('', context['resources_select_inputs'][1]['error'])

        self.assertEqual('app_namespace:resources_manage_resources', context['next_controller'])

        self.assertIn('license_to_consultant_map', context)

        self.assertEqual('consultant', context['hide_consultant_licenses'][0])

        self.assertEqual({}, context['organization_status_toggle']['attributes'])
        self.assertEqual('', context['organization_status_toggle']['classes'])
        self.assertEqual('organization-status', context['organization_status_toggle']['name'])
        self.assertEqual('Status', context['organization_status_toggle']['display_text'])
        self.assertEqual('Active', context['organization_status_toggle']['on_label'])
        self.assertEqual('Inactive', context['organization_status_toggle']['off_label'])
        self.assertEqual('primary', context['organization_status_toggle']['on_style'])
        self.assertEqual('default', context['organization_status_toggle']['off_style'])
        self.assertEqual('medium', context['organization_status_toggle']['size'])
        self.assertIn('initial', context['organization_status_toggle'])
        self.assertFalse(context['organization_status_toggle']['disabled'])
        self.assertEqual('', context['organization_status_toggle']['error'])

    @mock.patch.object(AppUsersViewMixin, 'get_organization_model')
    def test_handle_modify_user_requests_cannot_create_error(self, mock_get_org_model):
        organization = mock.MagicMock()
        organization.LICENSES = mock.MagicMock()
        organization.LICENSES.list.return_value = []
        mock_get_org_model.return_value = organization

        self.request.GET = {'next': 'unknown'}

        CustomModifyOrganization()._handle_modify_user_requests(self.request)

        msg_args = self.mock_messages.error.call_args_list
        self.assertEqual("We're sorry, but you are unable to create new organizations at this time.", msg_args[0][0][1])
        self.mock_reverse.assert_called()
        self.assertEqual('app_namespace:app_users_manage_organizations', self.mock_reverse.call_args[0][0])
        self.mock_redirect.assert_called()
