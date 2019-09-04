"""
********************************************************************************
* Name: condor_workflow_manager_tests.py
* Author: mlebaron
* Created On: September 4, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import mock
from tethysext.atcore.services.condor_workflow_manager import ResourceWorkflowCondorJobManager as Manager
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.models.app_users import ResourceWorkflowStep
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class CondorWorkflowManagerTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()

        self.model_db = mock.MagicMock()
        self.model_db.db_url = 'some_url'

        self.step = ResourceWorkflowStep()

        self.user = mock.MagicMock()

        self.working_directory = 'path/to/dir'

        self.app = mock.MagicMock()

        self.scheduler_name = 'some_scheduler'

    def tearDown(self):
        super().tearDown()

    def test_init_no_jobs(self):
        try:
            Manager(self.session, self.model_db, self.step, self.user, self.working_directory, self.app,
                    self.scheduler_name, jobs=None)
            self.assertTrue(False)  # This line should not be reached
        except ValueError as e:
            self.assertEqual('Argument "jobs" is not defined or empty. Must provide at least one CondorWorkflowJobNode '
                             'or equivalent dictionary.', str(e))
