from unittest import mock
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SpatialCondorJobRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        m = mock.MagicMock()
        m.__reduce__ = lambda self: (mock.MagicMock, ())
        self.instance = SpatialCondorJobRWS(geoserver_name='', map_manager=m, spatial_manager=m)

    def test_query(self):
        self.session.add(self.instance)
        self.session.commit()
        ret = self.session.query(SpatialCondorJobRWS).get(self.instance.id)
        self.assertEqual(self.instance, ret)

    def test_default_options(self):
        baseline = {
            'scheduler': '',
            'jobs': [],
            'workflow_kwargs': {},
            'working_message': '',
            'error_message': '',
            'pending_message': '',
            'lock_workflow_on_job_submit': False,
            'lock_resource_on_job_submit': False,
            'unlock_workflow_on_job_submit': False,
            'unlock_resource_on_job_submit': False,
            'lock_workflow_on_job_complete': False,
            'lock_resource_on_job_complete': False,
            'unlock_workflow_on_job_complete': False,
            'unlock_resource_on_job_complete': False,
            'workflow_lock_required': False,
            'release_workflow_lock_on_completion': True,
            'release_workflow_lock_on_init': False,
            'resource_lock_required': False,
            'release_resource_lock_on_completion': True,
            'release_resource_lock_on_init': False,
            'geocode_enabled': False,
            'label_options': None,
        }

        self.assertDictEqual(baseline, self.instance.default_options)

    def test_init_parameters(self):
        self.assertDictEqual({}, self.instance.init_parameters())

    @mock.patch('tethysext.atcore.models.resource_workflow_steps.spatial_condor_job_rws.SpatialResourceWorkflowStep.validate')  # noqa: E501
    def test_validate(self, mock_super_validate):
        self.instance.validate()
        mock_super_validate.assert_called()
