from unittest import mock
from tethysext.atcore.models.resource_workflow_steps import ResultsResourceWorkflowStep
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests,\
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResultsResourceWorkflowStepTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.instance = ResultsResourceWorkflowStep()

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(ResultsResourceWorkflowStep).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    def test_default_options(self):
        self.assertDictEqual({}, self.instance.default_options)

    def test_init_parameters(self):
        self.assertDictEqual({}, self.instance.init_parameters())

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.results_rws.ResourceWorkflowStep.reset')
    def test_reset(self, mock_super_reset):
        result = ResourceWorkflowResult()
        result.reset = mock.MagicMock()
        self.instance.results.append(result)

        self.instance.reset()

        result.reset.assert_called()
        mock_super_reset.assert_called()
