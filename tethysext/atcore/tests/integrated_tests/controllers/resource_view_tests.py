"""
********************************************************************************
* Name: resource_view_tests.py
* Author: mlebaron
* Created On: August 5, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory
from django.contrib.auth.models import User
from tethysext.atcore.controllers.resource_view import ResourceView
from tethysext.atcore.models.app_users import AppUser, Resource
from tethysext.atcore.services.model_database import ModelDatabase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class MockedModelDbMixin:

    def get_model_db(self, request, resource, *args, **kwargs):
        return mock.MagicMock(spec=ModelDatabase)


class OnGetOverriderViewHttpResponse(ResourceView):
    response = mock.MagicMock(spec=HttpResponse)

    def on_get(self, request, session, resource):
        return self.response


class OnGetOverriderViewNonHttpResponse(MockedModelDbMixin, ResourceView):
    response = mock.MagicMock()

    def on_get(self, request, session, resource):
        return self.response


class MethodMappingView(MockedModelDbMixin, ResourceView):
    template_name = 'foo.html'
    view_title = 'Title'
    view_subtitle = 'Subtitle'
    response = mock.MagicMock(spec=HttpResponse)

    def my_magic_method(self, request, session, resource, back_url):
        return self.response


class NoTitlesView(MockedModelDbMixin, ResourceView):
    template_name = 'foo.html'
    response = mock.MagicMock(spec=HttpResponse)


class ResourceViewTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()
        self.username = 'user1'
        self.role = AppUser.ROLES.ORG_USER
        self.is_active = True

        self.django_user = User.objects.create(username=self.username, password='pass')
        self.app_user = AppUser(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
        )
        self.session.add(self.app_user)

        self.resource = Resource(
            name='Foo',
            description='Bar',
            created_by=self.username
        )
        self.session.add(self.resource)
        self.session.commit()

        self.resource_id = str(self.resource.id)

        self.mock_app = mock.MagicMock()
        self.mock_app.get_persistent_store_database().return_value = self.session

        dbu_patcher = mock.patch(
            'tethysext.atcore.controllers.app_users.mixins.ResourceViewMixin.default_back_url',
            return_value='/bar/'
        )
        dbu_patcher.start()
        self.addCleanup(dbu_patcher.stop)

        render_patcher = mock.patch('tethysext.atcore.controllers.resource_view.render')
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

        can_view_patcher = mock.patch('tethysext.atcore.models.app_users.app_user.AppUser.can_view', return_value=True)
        can_view_patcher.start()
        self.addCleanup(can_view_patcher.stop)

    def tearDown(self):
        super().tearDown()

    def test_get(self):
        request = self.request_factory.get('/foo/')
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(MethodMappingView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        self.assertEqual(self.mock_render(), response)
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Title', context['nav_title'])
        self.assertEqual('Subtitle', context['nav_subtitle'])
        self.assertEqual(self.resource.id, context['resource'].id)

    def test_get_no_titles(self):
        request = self.request_factory.get('/foo/')
        request.user = self.django_user
        controller = NoTitlesView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(NoTitlesView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        self.assertEqual(self.mock_render(), response)
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Foo', context['nav_title'])
        self.assertEqual('', context['nav_subtitle'])
        self.assertEqual(self.resource.id, context['resource'].id)

    def test_get_on_get_HttpResponse(self):
        request = self.request_factory.get('/foo/')
        request.user = self.django_user
        controller = OnGetOverriderViewHttpResponse.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIs(OnGetOverriderViewHttpResponse.response, response)

    def test_get_on_get_not_HttpResponse(self):
        request = self.request_factory.get('/foo/')
        request.user = self.django_user
        controller = OnGetOverriderViewNonHttpResponse.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(OnGetOverriderViewNonHttpResponse.response, response)
        self.assertIs(self.mock_render(), response)

    def test_get_request_to_method_exists(self):
        request = self.request_factory.get('/foo/', data={'method': 'my-magic-method'})
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIs(MethodMappingView.response, response)

    def test_get_request_to_method_not_exists(self):
        request = self.request_factory.get('/foo/', data={'method': 'does-not-exist'})
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(MethodMappingView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Title', context['nav_title'])
        self.assertEqual('Subtitle', context['nav_subtitle'])
        self.assertEqual(self.resource.id, context['resource'].id)

    def test_get_no_resource(self):
        request = self.request_factory.get('/foo/', data={'method': 'does-not-exist'})
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request)

        self.assertIsNot(MethodMappingView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Title', context['nav_title'])
        self.assertEqual('Subtitle', context['nav_subtitle'])
        self.assertIsNone(context['resource'])

    def test_post(self):
        request = self.request_factory.post('/foo/', data={'method': 'my-magic-method'})
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIs(MethodMappingView.response, response)

    def test_post_no_method(self):
        request = self.request_factory.post('/foo/', data={'method': 'does-not-exist'})
        request.user = self.django_user
        controller = MethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsInstance(response, HttpResponseNotFound)

    def test_request_to_method_post(self):
        request = self.request_factory.post('/foo/', data={'method': 'on-get'})

        response = ResourceView().request_to_method(request)

        self.assertEqual('on_get', response.__name__)

    def test_request_to_method_get(self):
        request = self.request_factory.get('/foo/', data={'method': 'on-get'})

        response = ResourceView().request_to_method(request)

        self.assertEqual('on_get', response.__name__)

    def test_request_to_method_different_method(self):
        mock_request = mock.MagicMock()
        mock_request.method = 'SOMETHING'

        ret = ResourceView().request_to_method(mock_request)

        self.assertEqual(None, ret)

    def test_request_to_method_method_not_found(self):
        request = self.request_factory.get('/foo/', data={'method': 'does-not-exist'})

        ret = ResourceView().request_to_method(request)

        self.assertEqual(None, ret)

    def test_on_get(self):
        ret = ResourceView().on_get(None, None, None)

        self.assertEqual(None, ret)

    def test_get_model_db_no_resource(self):
        with self.assertRaises(RuntimeError) as e:
            ResourceView().get_model_db(None, None)
            self.assertIn('A resource with database_id attribute is required: Resource', e.exception.message)

    def test_get_model_db_no_db_id(self):
        error_thrown = False

        try:
            ResourceView().get_model_db(None, self.resource)
        except RuntimeError:
            error_thrown = True

        self.assertTrue(error_thrown)

    def test_get_model_db(self):
        self.resource.set_attribute('database_id', '123456')

        ret = ResourceView().get_model_db(None, self.resource)

        self.assertIsInstance(ret, ModelDatabase)
        self.assertEqual(self.resource.get_attribute('database_id'), ret.database_id)

    def test_get_context(self):
        context = {'key': 'val'}

        ret = ResourceView().get_context(None, None, None, context, None)

        self.assertEqual(context, ret)

    def test_get_permissions(self):
        permissions = {'key': 'val'}

        ret = ResourceView().get_permissions(None, permissions, None)

        self.assertEqual(permissions, ret)
