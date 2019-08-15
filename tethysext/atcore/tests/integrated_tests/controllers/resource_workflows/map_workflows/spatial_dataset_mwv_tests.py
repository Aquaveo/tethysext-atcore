"""
********************************************************************************
* Name: spatial_data_mwv_tests.py
* Author: mlebaron
* Created On: August 15, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
from django.http import HttpRequest
from tethysext.atcore.controllers.resource_workflows.map_workflows.spatial_dataset_mwv import SpatialDatasetMWV
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.models.app_users.resource_workflow_step import ResourceWorkflowStep
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialDataMwvTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.request = mock.MagicMock(spec=HttpRequest)
        self.resource = Resource()
        self.back_url = './back'
        self.next_url = './next'
        self.current_url = './current'

        self.workflow = ResourceWorkflow(name='foo')

        self.step1 = ResourceWorkflowStep(
            name='name1',
            help='help1',
            order=1
        )
        self.workflow.steps.append(self.step1)

        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def test_get_popup_form(self):
        SpatialDatasetMWV().get_popup_form(self.request, self.workflow.id, self.step1.id, back_url=self.back_url,
                                           resource=self.resource, session=self.session)
