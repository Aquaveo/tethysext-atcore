from unittest import mock
from tethysext.atcore.models.app_users import ResourceWorkflowResult
from tethysext.atcore.controllers.resource_workflows.workflow_results_view import WorkflowResultsView  # noqa: E501
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class NotResourceWorkflowResult:
    pass


class AnotherResourceWorkflowResult(ResourceWorkflowResult):
    pass


class WorkflowResultsViewTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = WorkflowResultsView()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.get_result_url_name')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.build_result_cards')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.WorkflowResultsView.validate_result')  # noqa: E501
    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.ResultViewMixin.get_result')
    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.get_context')
    def test_get_context(self, mock_get_context, mock_get_result, mock_validate, mock_build_result_cards, mock_result_url):  # noqa: E501
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_resource = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_workflow_id = mock.MagicMock()
        mock_step_id = mock.MagicMock()
        mock_result_id = mock.MagicMock()

        mock_current_step = mock.MagicMock(workflow='foo')

        mock_get_context.return_value = {'current_step': mock_current_step}
        mock_result = mock.MagicMock()
        mock_get_result.return_value = mock_result
        mock_build_result_cards.return_value = 'baz'
        mock_result_url.return_value = 'bar'

        # Function Call
        ret = self.instance.get_context(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
            result_id=mock_result_id
        )

        # Assert all calls happened properly

        mock_get_context.assert_called_with(
            request=mock_request,
            session=mock_session,
            resource=mock_resource,
            context=mock_context,
            model_db=mock_model_db,
            workflow_id=mock_workflow_id,
            step_id=mock_step_id,
        )

        mock_get_result.assert_called_with(
            request=mock_request,
            result_id=mock_result_id,
            session=mock_session
        )

        mock_validate.assert_called_with(
            request=mock_request,
            session=mock_session,
            result=mock_result
        )

        mock_current_step.set_last_result.assert_called_with(mock_result)
        mock_session.commit.assert_called()
        mock_build_result_cards.assert_called_with(mock_current_step)
        mock_result_url.assert_called_with(mock_request, mock_current_step.workflow)
        baseline = {
            'current_step': mock_current_step,
            'layers': mock_get_result().layers,
            'results': 'baz',
            'result_url_name': 'bar'
        }
        self.assertDictEqual(baseline, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_results_view.get_active_app')  # noqa: E501
    def test_get_result_url_name(self, mock_get_active_app):
        mock_request = mock.MagicMock()
        mock_workflow = mock.MagicMock(type='bar')
        mock_get_active_app.return_value = mock.MagicMock(package='foo')
        baseline = 'foo:bar_workflow_step_result'
        ret = WorkflowResultsView.get_result_url_name(mock_request, mock_workflow)
        self.assertEqual(baseline, ret)
        mock_get_active_app.assert_called_with(mock_request)

    def test_build_result_cards(self):
        mock_step = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.id = 'foo'
        mock_result.name = 'bar'
        mock_result.description = 'baz'
        mock_result.type = 'qux'
        mock_step.results = [mock_result]
        baseline = [
            {'id': 'foo',
             'name': 'bar',
             'description': 'baz',
             'type': 'qux'
             }
        ]
        ret = self.instance.build_result_cards(mock_step)
        self.assertEqual(baseline, ret)

    def test_validate_result_valid(self):
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_result = mock.MagicMock(spec=ResourceWorkflowResult)
        error_thrown = False

        try:
            self.instance.validate_result(mock_request, mock_session, mock_result)
        except TypeError:
            error_thrown = True

        self.assertFalse(error_thrown)

    def test_validate_result_invalid(self):
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_result = NotResourceWorkflowResult()
        error_thrown = False
        error_message = ''

        try:
            self.instance.validate_result(mock_request, mock_session, mock_result)
        except TypeError as e:
            error_thrown = True
            error_message = str(e)

        expected_message = 'Invalid result type for view: "NotResourceWorkflowResult". ' \
                           'Must be one of "ResourceWorkflowResult".'
        self.assertTrue(error_thrown)
        self.assertEqual(expected_message, error_message)

    def test_validate_result_multiple_valid(self):
        self.instance.valid_result_classes.append(AnotherResourceWorkflowResult)
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_result = mock.MagicMock(spec=ResourceWorkflowResult)
        error_thrown = False

        try:
            self.instance.validate_result(mock_request, mock_session, mock_result)
        except TypeError:
            error_thrown = True

        self.assertFalse(error_thrown)

    def test_validate_result_multiple_invalid(self):
        self.instance.valid_result_classes.append(AnotherResourceWorkflowResult)
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_result = NotResourceWorkflowResult()
        error_thrown = False
        error_message = ''

        try:
            self.instance.validate_result(mock_request, mock_session, mock_result)
        except TypeError as e:
            error_thrown = True
            error_message = str(e)

        expected_message = 'Invalid result type for view: "NotResourceWorkflowResult". ' \
                           'Must be one of "ResourceWorkflowResult", "AnotherResourceWorkflowResult".'
        self.assertTrue(error_thrown)
        self.assertEqual(expected_message, error_message)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.workflow_view.ResourceWorkflowView.process_step_data')
    def test_process_step_data(self, mock_process_step_data):
        mock_request = mock.MagicMock()
        mock_session = mock.MagicMock()
        mock_step = mock.MagicMock()
        mock_model_db = mock.MagicMock()
        mock_current_url = mock.MagicMock()
        mock_previous_url = mock.MagicMock()
        mock_next_url = mock.MagicMock()
        baseline = ''
        mock_process_step_data.return_value = baseline
        mock_step.ROOT_STATUS_KEY = 'foo'
        mock_step.STATUS_COMPLETE = 'bar'

        ret = self.instance.process_step_data(
            mock_request,
            mock_session,
            mock_step,
            mock_model_db,
            mock_current_url,
            mock_previous_url,
            mock_next_url
        )

        mock_session.commit.assert_called()
        mock_step.set_status.assert_called_with(mock_step.ROOT_STATUS_KEY, mock_step.STATUS_COMPLETE)
        mock_process_step_data.assert_called_with(
            request=mock_request,
            session=mock_session,
            step=mock_step,
            model_db=mock_model_db,
            current_url=mock_current_url,
            previous_url=mock_previous_url,
            next_url=mock_next_url
        )
        self.assertEqual(baseline, ret)
