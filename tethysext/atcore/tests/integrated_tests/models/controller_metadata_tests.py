from unittest import mock
from tethys_sdk.base import TethysController
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.controller_metadata import ControllerMetadata
from tethysext.atcore.controllers.app_users.mixins import ResourceViewMixin
from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class FakeController(TethysController):
    foo = 'foo'
    bar = 'bar'


class FakeResourceViewMixin(ResourceViewMixin):
    foo = 'foo'
    bar = 'bar'


class FakeResourceWorkflowView(ResourceWorkflowView):
    foo = 'foo'
    bar = 'bar'


class ControllerMetadataTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.controller_kwargs = {'foo': 'goo'}

        self.instance = ControllerMetadata(
            kwargs=self.controller_kwargs
        )
        self.session.add(self.instance)
        self.session.commit()

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeController.as_controller')  # noqa: E501
    def test_instantiate(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeController'
        ret = self.instance.instantiate()
        mock_as_controller.assert_called_with(**self.controller_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeController.as_controller')  # noqa: E501
    def test_instantiate_with_kwargs(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeController'
        ret = self.instance.instantiate(bar='baz')
        expected_kwargs = {'foo': 'goo', 'bar': 'baz'}
        mock_as_controller.assert_called_with(**expected_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceWorkflowView.as_controller')  # noqa: E501
    def test_instantiate_ResourceWorkflowView(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceWorkflowView'  # noqa: E501
        ret = self.instance.instantiate()
        mock_as_controller.assert_called_with(**self.controller_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceWorkflowView.as_controller')  # noqa: E501
    def test_instantiate_ResourceWorkflowView_with_kwargs(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceWorkflowView'  # noqa: E501
        ret = self.instance.instantiate(bar='baz')
        expected_kwargs = {'foo': 'goo', 'bar': 'baz'}
        mock_as_controller.assert_called_with(**expected_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceViewMixin.as_controller')  # noqa: E501
    def test_instantiate_ResourceViewMixin(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceViewMixin'  # noqa: E501
        ret = self.instance.instantiate()
        mock_as_controller.assert_called_with(**self.controller_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    @mock.patch('tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceViewMixin.as_controller')  # noqa: E501
    def test_instantiate_ResourceViewMixin_with_kwargs(self, mock_as_controller):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.FakeResourceViewMixin'  # noqa: E501
        ret = self.instance.instantiate(bar='baz')
        expected_kwargs = {'foo': 'goo', 'bar': 'baz'}
        mock_as_controller.assert_called_with(**expected_kwargs)
        self.assertEqual(mock_as_controller(), ret)

    def test_instantiate_ImportError_not_in_existing_module(self):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.controller_metadata_tests.ControllerDoesNotExist'  # noqa: E501
        self.assertRaises(ImportError, self.instance.instantiate)

    def test_instantiate_ImportError_module_dne(self):
        self.instance.path = 'tethysext.atcore.tests.integrated_tests.models.fake_module.FakeController'
        self.assertRaises(ImportError, self.instance.instantiate)
