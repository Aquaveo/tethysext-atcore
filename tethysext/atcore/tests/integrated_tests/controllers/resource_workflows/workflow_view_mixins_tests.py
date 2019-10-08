"""
********************************************************************************
* Name: mixins.py
* Author: Tanner, mlebaron
* Created On: May 7, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import unittest
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.controllers.resource_workflows.mixins import ResultViewMixin
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ClassWithWorkflowMixin(WorkflowViewMixin):
    pass


class ClassWithResultViewMixin(ResultViewMixin):
    pass


class WorkflowViewMixinTests(unittest.TestCase):

    def setUp(self):
        self.instance = ClassWithWorkflowMixin()

    def tearDown(self):
        pass

    def test_get_resource_workflow_model(self):
        ret = self.instance.get_resource_workflow_model()
        self.assertIs(ResourceWorkflow, ret)

    def test_get_resource_workflow_step_model(self):
        ret = self.instance.get_resource_workflow_step_model()
        self.assertIs(ResourceWorkflowStep, ret)

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_resource_workflow_model')
    def test_get_workflow_with_session(self, mock_get_rw_model):
        mock_get_rw_model.return_value = ResourceWorkflow
        mock_session = mock.MagicMock()

        ret = self.instance.get_workflow(request=mock.MagicMock(), workflow_id='valid workflow id',
                                         session=mock_session)

        self.assertEqual(mock_session.query().filter().one(), ret)
        mock_session.close.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_resource_workflow_model')
    def test_get_workflow_no_session(self, mock_get_rw_model):
        mock_get_rw_model.return_value = ResourceWorkflow
        self.instance.get_sessionmaker = mock.MagicMock()
        mock_session = self.instance.get_sessionmaker()()

        ret = self.instance.get_workflow(request=mock.MagicMock(), workflow_id='valid workflow id', session=None)

        self.instance.get_sessionmaker.assert_called()
        self.instance.get_sessionmaker().assert_called()
        self.assertEqual(mock_session.query().filter().one(), ret)
        mock_session.close.assert_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_resource_workflow_step_model')  # noqa: E501
    def test_get_step_with_session(self, mock_get_rw_step_model):
        mock_get_rw_step_model.return_value = ResourceWorkflowStep
        mock_session = mock.MagicMock()

        ret = self.instance.get_step(request=mock.MagicMock(), step_id='valid step id', session=mock_session)

        self.assertEqual(mock_session.query().filter().one(), ret)
        mock_session.close.assert_not_called()

    @mock.patch('tethysext.atcore.controllers.resource_workflows.mixins.WorkflowViewMixin.get_resource_workflow_step_model')  # noqa: E501
    def test_get_step_no_session(self, mock_get_rw_step_model):
        mock_get_rw_step_model.return_value = ResourceWorkflowStep
        self.instance.get_sessionmaker = mock.MagicMock()
        mock_session = self.instance.get_sessionmaker()()

        ret = self.instance.get_step(request=mock.MagicMock(), step_id='valid step id', session=None)

        self.instance.get_sessionmaker.assert_called()
        self.instance.get_sessionmaker().assert_called()
        self.assertEqual(mock_session.query().filter().one(), ret)
        mock_session.close.assert_called()
