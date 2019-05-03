from unittest import mock
import uuid
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep, ResourceWorkflowResult


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        # Custom setup here
        self.workflow = ResourceWorkflow(name='bar')

        # Build the steps and save in the workflow
        # Status will be set dynamically to allow for easy testing.
        self.step_1 = ResourceWorkflowStep(name='foo', help='step_1', order=1)
        self.step_2 = ResourceWorkflowStep(name='bar', help='step_2', order=2)
        self.step_3 = ResourceWorkflowStep(name='baz', help='step_3', order=3)
        self.step_4 = ResourceWorkflowStep(name='invalid_step', help='invalid step 4', order=4)
        self.workflow.steps = [self.step_1, self.step_2, self.step_3]

        # Build the results and save in the workflow
        self.result_1 = ResourceWorkflowResult(name='foo', description='lorem_1', data={'baz': 1})
        self.result_2 = ResourceWorkflowResult(name='bar', description='lorem_2', data={'baz': 2})
        self.result_3 = ResourceWorkflowResult(name='baz', description='lorem_3', data={'baz': 3})
        self.result_4 = ResourceWorkflowResult(name='invalid_step', description='invalid step 4', data={'baz': 4})
        self.workflow.results = [self.result_1, self.result_2, self.result_3]

        self.session.add(self.workflow)
        self.session.commit()

    def test___str__(self):
        ret = str(self.workflow)
        self.assertEqual('<ResourceWorkflow id={} name=bar>'.format(self.workflow.id), ret)

    def test_get_next_step_no_steps(self):
        self.workflow.steps = []
        idx, ret = self.workflow.get_next_step()
        self.assertIsNone(ret)
        self.assertEqual(0, idx)

    def test_get_next_step_no_root_status(self):
        self.step_1.set_status(ResourceWorkflowStep.ROOT_STATUS_KEY, None)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    def test_get_next_step_multiple_first_complete(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

    def test_get_next_step_multiple_step_all_complete(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        self.workflow.steps[2].set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_COMPLETE)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

    def test_get_next_step_one_step_complete(self):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.workflow.steps = [self.step_1]
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    def test_get_next_step_one_step_not_complete(self):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_PENDING)
        self.workflow.steps = [self.step_1]
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(0, idx)
        self.assertEqual(self.step_1, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_first_step_pending(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_PENDING)
        mock_next_step.return_value = (0, self.step_1)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_PENDING, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_first_step_not_pending(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_ERROR)
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_PENDING)
        mock_next_step.return_value = (0, self.step_1)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_ERROR, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.ResourceWorkflow.get_next_step')
    def test_get_status_not_first_step(self, mock_next_step):
        self.step_1.set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_COMPLETE)
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_PENDING)
        mock_next_step.return_value = (1, self.step_2)
        ret = self.workflow.get_status()
        self.assertEqual(self.workflow.STATUS_CONTINUE, ret)

    def test_get_adjacent_steps_first_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_1)
        self.assertIsNone(prev_step)
        self.assertEqual(next_step, self.step_2)

    def test_get_adjacent_steps_middle_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_2)
        self.assertEqual(prev_step, self.step_1)
        self.assertEqual(next_step, self.step_3)

    def test_get_adjacent_steps_last_step(self):
        prev_step, next_step = self.workflow.get_adjacent_steps(self.step_3)
        self.assertEqual(prev_step, self.step_2)
        self.assertIsNone(next_step)

    def test_get_adjacent_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_adjacent_steps, self.step_4)

    def test_get_previous_steps_first_step(self):
        ret = self.workflow.get_previous_steps(self.step_1)
        self.assertListEqual([], ret)

    def test_get_previous_steps_middle_step(self):
        ret = self.workflow.get_previous_steps(self.step_2)
        self.assertListEqual([self.step_1], ret)

    def test_get_previous_steps_last_step(self):
        ret = self.workflow.get_previous_steps(self.step_3)
        self.assertListEqual([self.step_1, self.step_2], ret)

    def test_get_previous_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_previous_steps, self.step_4)

    def test_get_last_result_not_stored(self):
        ret = self.workflow.get_last_result()
        self.assertEqual(self.result_1, ret)

    def test_get_last_result_stored(self):
        self.workflow.set_attribute(self.workflow.ATTR_LAST_RESULT, str(self.result_2.id))
        ret = self.workflow.get_last_result()
        self.assertEqual(self.result_2, ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.log')
    def test_get_last_result_invalid_id_stored(self, mock_log):
        bad_id = str(uuid.uuid4())
        self.workflow.set_attribute(self.workflow.ATTR_LAST_RESULT, bad_id)
        ret = self.workflow.get_last_result()
        self.assertIsNone(ret)
        mock_log.warning.assert_called_with('Result with id "{}" not in workflow'.format(bad_id))

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.log')
    def test_get_last_result_workflow_has_no_results(self, mock_log):
        self.workflow.results = []
        self.session.commit()
        ret = self.workflow.get_last_result()
        self.assertIsNone(ret)
        mock_log.warning.assert_called_with('Workflow has no results.')

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.log')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.Session')
    def test_get_last_result_invalid_session(self, mock_Session, mock_log):
        mock_Session.object_session.return_value = None
        self.workflow.set_attribute(self.workflow.ATTR_LAST_RESULT, str(self.result_2.id))
        ret = self.workflow.get_last_result()
        self.assertIsNone(ret)
        mock_log.error.assert_called_with("Could not get session from workflow: 'NoneType' object has "
                                          "no attribute 'query'")

    def test_set_last_result(self):
        self.workflow.set_last_result(self.result_2)
        received = self.workflow.get_attribute(self.workflow.ATTR_LAST_RESULT)
        self.assertEqual(str(self.result_2.id), received)

    def test_set_last_result_invalid_result(self):
        self.assertRaises(ValueError, self.workflow.set_last_result, self.result_4)

    def test_get_adjacent_results_first(self):
        prev_result, next_result = self.workflow.get_adjacent_results(self.result_1)
        self.assertIsNone(prev_result)
        self.assertEqual(self.result_2, next_result)

    def test_get_adjacent_results_middle(self):
        prev_result, next_result = self.workflow.get_adjacent_results(self.result_2)
        self.assertEqual(self.result_1, prev_result)
        self.assertEqual(self.result_3, next_result)

    def test_get_adjacent_results_last(self):
        prev_result, next_result = self.workflow.get_adjacent_results(self.result_3)
        self.assertEqual(self.result_2, prev_result)
        self.assertIsNone(next_result)

    def test_get_adjacent_results_invalid_result(self):
        self.assertRaises(ValueError, self.workflow.get_adjacent_results, self.result_4)
