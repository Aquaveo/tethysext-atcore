from .common import RWS_DEFAULT_OPTIONS
from tethysext.atcore.models.resource_workflow_steps import SetStatusRWS
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests,\
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class SetStatusRWSTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.ssrws_no_options = SetStatusRWS(
            name='ssrws_no_options',
            help='No options specified',
            order=1,
        )

        self.ssrws_three_statuses = SetStatusRWS(
            name='ssrws_three_statuses',
            help='Three statuses',
            order=2,
            options={
                'statuses': [
                    {'status': SetStatusRWS.STATUS_APPROVED,
                     'label': 'Approve'},
                    {'status': SetStatusRWS.STATUS_CHANGES_REQUESTED},
                    {'status': SetStatusRWS.STATUS_REJECTED,
                     'label': None},
                ]
            },
        )

        self.ssrws_custom_titles = SetStatusRWS(
            name='ssrws_custom_titles',
            help='help3',
            order=3,
            options={
                'form_title': 'Custom Title',
                'status_label': 'Choose One',
            }
        )

        self.ssrws_invalid_status_dict = SetStatusRWS(
            name='ssrws_invalid_status_dict',
            help='help4',
            order=4,
            options={
                'statuses': [{'label': 'foo'}]
            }
        )

        self.ssrws_invalid_status = SetStatusRWS(
            name='ssrws_invalid_status',
            help='help5',
            order=5,
            options={
                'statuses': [{'status': SetStatusRWS.STATUS_DIRTY}]
            }
        )

        self.session.add(self.ssrws_no_options)
        self.session.add(self.ssrws_three_statuses)
        self.session.add(self.ssrws_custom_titles)
        self.session.add(self.ssrws_invalid_status_dict)
        self.session.add(self.ssrws_invalid_status)
        self.session.commit()

    def test_default_options(self):
        ret = self.ssrws_no_options.default_options
        default_options = {
            'form_title': None,
            'status_label': None,
            'statuses': [
                {'status': SetStatusRWS.STATUS_COMPLETE,
                 'label': None}
            ],
            **RWS_DEFAULT_OPTIONS
        }
        self.assertDictEqual(default_options, ret)

    def test_init_parameters(self):
        ret = self.ssrws_no_options.init_parameters()

        initial_parameters = {
            'comments': {
                'help': 'Comments on reason for changing status to this status.',
                'value': '',

                'required': False
            },
        }
        self.assertDictEqual(initial_parameters, ret)

    def test_validate_statuses_ssrws_no_options(self):
        error_raised = False

        try:
            self.ssrws_no_options.validate_statuses()
        except RuntimeError:
            error_raised = True

        self.assertFalse(error_raised)

    def test_validate_statuses_ssrws_three_statuses(self):
        error_raised = False

        try:
            self.ssrws_three_statuses.validate_statuses()
        except RuntimeError:
            error_raised = True

        self.assertFalse(error_raised)

    def test_validate_statuses_ssrws_custom_titles(self):
        error_raised = False

        try:
            self.ssrws_custom_titles.validate_statuses()
        except RuntimeError:
            error_raised = True

        self.assertFalse(error_raised)

    def test_validate_statuses_ssrws_invalid_status_dict(self):
        with self.assertRaises(RuntimeError) as cm:
            self.ssrws_invalid_status_dict.validate_statuses()

        self.assertIn('Key "status" not found in status dict provided by option "statuses": ', str(cm.exception))

    def test_validate_statuses_ssrws_invalid_status(self):
        with self.assertRaises(RuntimeError) as cm:
            self.ssrws_invalid_status.validate_statuses()

        self.assertEqual('Status "Dirty" is not a valid status for SetStatusRWS. Must be one of: '
                         'Pending, Working, Error, Failed, Complete, Submitted, Under Review, '
                         'Approved, Rejected, Changes Requested, Reviewed', str(cm.exception))
