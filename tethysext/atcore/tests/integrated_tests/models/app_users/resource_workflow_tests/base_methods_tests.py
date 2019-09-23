from unittest import mock
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep, ResourceWorkflowResult


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowBaseMethodsTests(SqlAlchemyTestCase):

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
        self.result_1 = ResourceWorkflowResult(name='foo', description='lorem_1', _data={'baz': 1})
        self.result_2 = ResourceWorkflowResult(name='bar', description='lorem_2', _data={'baz': 2})
        self.result_3 = ResourceWorkflowResult(name='baz', description='lorem_3', _data={'baz': 3})
        self.result_4 = ResourceWorkflowResult(name='invalid_step', description='invalid step 4', _data={'baz': 4})
        self.workflow.results = [self.result_1, self.result_2, self.result_3]

        self.session.add(self.workflow)

        self.session.commit()

    def test___str__(self):
        ret = str(self.workflow)
        self.assertEqual(f'<ResourceWorkflow name="bar" id="{self.workflow.id}">', ret)

    def test_complete(self):
        # All other steps complete
        self.step_1.set_status(status=self.step_1.STATUS_COMPLETE)
        self.step_2.set_status(status=self.step_2.STATUS_COMPLETE)

        # Last step varies
        self.step_3.set_status(status=self.step_3.STATUS_PENDING)
        self.assertFalse(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_WORKING)
        self.assertFalse(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_ERROR)
        self.assertFalse(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_FAILED)
        self.assertFalse(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_COMPLETE)
        self.assertTrue(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_SUBMITTED)
        self.assertTrue(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_UNDER_REVIEW)
        self.assertFalse(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_APPROVED)
        self.assertTrue(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_REJECTED)
        self.assertTrue(self.workflow.complete)
        self.step_3.set_status(status=self.step_3.STATUS_CHANGES_REQUESTED)
        self.assertFalse(self.workflow.complete)

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

    def test_get_next_step_multiple_steps_non_COMPLETE_complete_statuses(self):
        self.workflow.steps[0].set_status(self.step_1.ROOT_STATUS_KEY, self.step_1.STATUS_SUBMITTED)
        self.workflow.steps[1].set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_APPROVED)
        self.workflow.steps[2].set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_PENDING)
        idx, ret = self.workflow.get_next_step()
        self.assertEqual(2, idx)
        self.assertEqual(self.step_3, ret)

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

    def test_get_next_steps(self):
        ret = self.workflow.get_next_steps(self.step_1)
        self.assertListEqual([self.step_2, self.step_3], ret)

    def test_get_next_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.get_next_steps, self.step_4)

    def test_reset_next_steps(self):
        self.step_2.set_status(self.step_2.ROOT_STATUS_KEY, self.step_2.STATUS_COMPLETE)
        self.step_3.set_status(self.step_3.ROOT_STATUS_KEY, self.step_3.STATUS_ERROR)

        self.workflow.reset_next_steps(self.step_1)

        self.assertEqual(self.step_2.STATUS_PENDING, self.step_2.get_status(self.step_2.ROOT_STATUS_KEY))
        self.assertEqual(self.step_3.STATUS_PENDING, self.step_3.get_status(self.step_3.ROOT_STATUS_KEY))

    def test_reset_next_steps_invalid_step(self):
        self.assertRaises(ValueError, self.workflow.reset_next_steps, self.step_4)
