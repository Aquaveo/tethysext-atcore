"""
********************************************************************************
* Name: mixins.py
* Author: mlebaron
* Created On: September 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from tethysext.atcore.models.app_users import ResourceWorkflow
from tethysext.atcore.controllers.resource_workflows.mixins import WorkflowViewMixin
from tethysext.atcore.controllers.resource_workflows.mixins import ResultViewMixin
from tethysext.atcore.models.app_users.resource_workflow_result import ResourceWorkflowResult
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
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


class ResultViewMixinTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.workflow = ResourceWorkflow()

        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def test_get_resource_result_model(self):
        ret = ClassWithResultViewMixin().get_resource_workflow_result_model()

        self.assertEqual(ret, ResourceWorkflowResult)

    @mock.patch('tethysext.atcore.controllers.app_users.mixins.AppUsersViewMixin.get_sessionmaker')
    def test_get_result_no_session(self, mock_get_session):
        request = mock.MagicMock()
        query = mock.MagicMock()
        xfilter = mock.MagicMock()
        one = mock.MagicMock()

        one.return_value = self.workflow
        xfilter.return_value = one
        query.return_value = xfilter

        mock_get_session.return_value = query

        ClassWithResultViewMixin().get_result(request, 'a')
