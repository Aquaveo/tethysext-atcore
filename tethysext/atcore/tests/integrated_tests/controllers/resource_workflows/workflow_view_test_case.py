"""
********************************************************************************
* Name: workflow_view_test_case.py
* Author: nswain
* Created On: October 02, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.models.app_users import Resource, ResourceWorkflow


class WorkflowViewTestCase(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.resource = Resource(name='foo')
        self.workflow = ResourceWorkflow(name='bar')
        self.workflow.resource = self.resource
