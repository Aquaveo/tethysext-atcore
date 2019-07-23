from unittest import mock
from django.http import HttpResponse
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


class OnGetOverriderView(ResourceView):
    response = mock.MagicMock(spec=HttpResponse)

    def on_get(self, request, session, resource):
        return self.response


class GetMethodMappingView(ResourceView):
    template_name = 'foo.html'
    view_title = 'Title'
    view_subtitle = 'Subtitle'
    response = mock.MagicMock(spec=HttpResponse)

    def my_magic_method(self, request, session, resource, back_url):
        return self.response

    def get_model_db(self, request, resource, *args, **kwargs):
        return mock.MagicMock(spec=ModelDatabase)


class NoTitlesView(ResourceView):
    pass


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
        controller = GetMethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(GetMethodMappingView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Title', context['nav_title'])
        self.assertEqual('Subtitle', context['nav_subtitle'])
        self.assertEqual(self.resource.id, context['resource'].id)

    def test_get_on_get_HttpResponse(self):
        request = self.request_factory.get('/foo/')
        request.user = self.django_user
        controller = OnGetOverriderView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIs(OnGetOverriderView.response, response)

    def test_get_on_get_not_HttpResponse(self):
        # request = self.request_factory.get('/foo/', resource_id=self.resource_id)
        # request.user = self.django_user
        # controller = OnGetOverriderView.as_controller(_app=self.mock_app)
        # response = controller(request)
        # self.assertIs(OnGetOverriderView.response, response)
        pass

    def test_get_request_to_method_exists(self):
        request = self.request_factory.get('/foo/', data={'method': 'my-magic-method'})
        request.user = self.django_user
        controller = GetMethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIs(GetMethodMappingView.response, response)

    def test_get_request_to_method_not_exists(self):
        request = self.request_factory.get('/foo/', data={'method': 'does-not-exist'})
        request.user = self.django_user
        controller = GetMethodMappingView.as_controller(_app=self.mock_app)

        response = controller(request, resource_id=self.resource_id)

        self.assertIsNot(GetMethodMappingView.response, response)
        render_calls = self.mock_render.call_args_list
        self.assertEqual(1, len(render_calls))
        template = render_calls[0][0][1]
        self.assertEqual('foo.html', template)
        context = render_calls[0][0][2]
        self.assertEqual('Title', context['nav_title'])
        self.assertEqual('Subtitle', context['nav_subtitle'])
        self.assertEqual(self.resource.id, context['resource'].id)

    def test_get_no_titles_defined(self):
        pass

