"""
********************************************************************************
* Name: helpers_tests.py
* Author: mlebaron
* Created On: September 3, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import mock
import unittest
from tethysext.atcore.services.resource_workflows import helpers
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from argparse import Namespace


class HelpersTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_set_step_status(self):
        session = mock.MagicMock()
        step = ResourceWorkflowStep(name='name1', help='help1', order=1)
        step.attributes = {'condor_job_statuses': [step.STATUS_PENDING]}

        helpers.set_step_status(session, step, step.STATUS_COMPLETE)

        self.assertEqual([step.STATUS_PENDING, step.STATUS_COMPLETE], step.get_attribute('condor_job_statuses'))

    @mock.patch('argparse._sys')
    def test_parse_workflow_step_args(self, mock_sys):
        mock_sys.argv = ['prog']
        ret = helpers.parse_workflow_step_args()

        self.assertIsInstance(ret, Namespace)
