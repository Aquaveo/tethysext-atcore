import json
from unittest import mock
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests
from tethysext.atcore.models.app_users import ResourceWorkflow, ResourceWorkflowStep


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceWorkflowStepTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        # Custom setup here
        #  Build the workflow
        self.workflow = ResourceWorkflow(name='bar')

        #  Build the step to test
        self.step = ResourceWorkflowStep(
            name='foo',
            help='step_0',
            order=1,
            # options={
            #     'geometry_source': {
            #         SpatialDatasetRWS.OPT_PARENT_STEP: {
            #             'parent_field': 'geometry'}
            #     }
            # }
        )
        self.session.add(self.step)

        self.workflow.steps = [self.step]
        self.session.add(self.workflow)
        self.session.commit()

    def test__repr__(self):
        blank_baseline = '<ResourceWorkflowStep name="{}" id="{}" >'.format(self.step.name, self.step.id)
        self.assertEqual(blank_baseline, repr(self.step))

    def test_complete(self):
        self.step.set_status(status=self.step.STATUS_PENDING)
        self.assertFalse(self.step.complete)
        self.step.set_status(status=self.step.STATUS_WORKING)
        self.assertFalse(self.step.complete)
        self.step.set_status(status=self.step.STATUS_ERROR)
        self.assertFalse(self.step.complete)
        self.step.set_status(status=self.step.STATUS_FAILED)
        self.assertFalse(self.step.complete)
        self.step.set_status(status=self.step.STATUS_COMPLETE)
        self.assertTrue(self.step.complete)
        self.step.set_status(status=self.step.STATUS_SUBMITTED)
        self.assertTrue(self.step.complete)
        self.step.set_status(status=self.step.STATUS_UNDER_REVIEW)
        self.assertFalse(self.step.complete)
        self.step.set_status(status=self.step.STATUS_APPROVED)
        self.assertTrue(self.step.complete)
        self.step.set_status(status=self.step.STATUS_REJECTED)
        self.assertTrue(self.step.complete)
        self.step.set_status(status=self.step.STATUS_CHANGES_REQUESTED)
        self.assertFalse(self.step.complete)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_to_dict(self, mock_init_params):
        # Test the abstract base class is empty by default
        baseline = {'parameters': {}}
        self.assertDictEqual(baseline, self.step.to_dict())

        mock_init_params.side_effect = [{
            'test_not_required_parameter': {
                'help': 'test parameter not required help.',
                'value': None,
                'required': False
            }}]
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        baseline = {
            'type': 'generic_workflow_step',
            'name': 'bar',
            'help': 'step_1',
            'parameters': {
                'test_not_required_parameter': None
            }
        }
        self.assertDictEqual(baseline, self.step.to_dict())

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_to_json(self, mock_init_params):
        # Test the abstract base class is empty by default
        baseline = json.dumps({'parameters': {}})
        self.assertEqual(baseline, self.step.to_json())

        mock_init_params.side_effect = [{
            'test_not_required_parameter': {
                'help': 'test parameter not required help.',
                'value': None,
                'required': False
            }}]
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        baseline = json.dumps({
            'type': 'generic_workflow_step',
            'name': 'bar',
            'help': 'step_1',
            'parameters': {
                "test_not_required_parameter": None}
        })

        self.assertEqual(baseline, self.step.to_json())

    def test_validate_valid(self):
        # Ensure the empty class is valid
        self.assertIsNone(self.step.validate())

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_validate_missing_required(self, mock_init_params):
        mock_init_params.return_value = {
            'test_parameter': {
                'help': 'test help.',
                'value': None,
                'required': True
            }
        }
        # rebuild Build the step to test with the mocked parameters.
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.assertRaises(ValueError, self.step.validate)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.set_parameter')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_parse_parameters(self, mock_init_params, mock_set_param):
        parameters = {
            'param_1': {
                'help': 'test parameter',
                'value': None,
                'required': False
            },
        }
        params = {'param_1': True, 'not_found_param': 'foo'}
        mock_init_params.return_value = parameters
        mock_set_param.side_effect = ['', ValueError]
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.step.parse_parameters(params)
        calls = [mock.call('param_1', True), mock.call('not_found_param', 'foo')]
        mock_set_param.assert_has_calls(calls)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.deepcopy')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_set_parameter(self, mock_init_params, mock_dc):
        parameters = {
            'param_1': {
                'help': 'test parameter',
                'value': None,
                'required': False
            },
        }
        mock_init_params.return_value = parameters
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)

        self.step.set_parameter(name='param_1', value=True)
        mock_dc.assert_called()

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_set_parameter_name_not_found(self, mock_init_params):
        parameters = {
            'param_1': {
                'help': 'test parameter',
                'value': None,
                'required': False
            },
        }
        mock_init_params.return_value = parameters
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.assertRaises(ValueError, self.step.set_parameter, name='param_not_found', value=True)

    def test_get_parameter_param_not_found_empty_class(self):
        # Test the blank class
        self.assertRaises(ValueError, self.step.get_parameter, 'foo')

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_get_parameter_modified_class(self, mock_init_params):
        parameters = {
            'param_1': {
                'help': 'test parameter',
                'value': None,
                'required': False
            },
        }
        mock_init_params.return_value = parameters
        self.step = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.step.set_parameter('param_1', True)
        self.assertTrue(self.step.get_parameter('param_1'))

    def test_get_parameters(self):
        baseline = {}
        self.step._parameter = baseline
        self.assertTrue(baseline is not self.step.get_parameters())

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option(self, mock_options, mock_parameter):
        parent = ResourceWorkflowStep(name='baz', help='step_2', order=2, )
        self.step = ResourceWorkflowStep(name='foo', help='step_0', order=1, parents=[parent])
        mock_options.get.return_value = {'parent': {'match_attr': 'name', 'match_value': 'baz'}}
        mock_parameter.return_value = 'param_value'
        ret = self.step.resolve_option('option')
        self.assertEqual('param_value', ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option_no_option_value(self, mock_options):
        mock_options.get.return_value = None
        self.assertIsNone(self.step.resolve_option('option'))
        mock_options.get.assert_called_with('option', None)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.get_parameter')
    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option_ValueError(self, mock_options, mock_parameter):
        parent = ResourceWorkflowStep(name='baz', help='step_2', order=2)
        self.step = ResourceWorkflowStep(name='foo', help='step_0', order=1, parents=[parent])
        mock_options.get.return_value = {'parent': {'match_attr': 'name', 'match_value': 'baz'}}
        mock_parameter.side_effect = ValueError
        self.assertRaises(RuntimeError, self.step.resolve_option, 'option')

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_reset(self, mock_init_parameters):
        mock_init_parameters.return_value = {}
        self.step = ResourceWorkflowStep(name='foo', help='step_0', order=1, dirty=True)
        self.step.set_status(ResourceWorkflowStep.ROOT_STATUS_KEY, ResourceWorkflowStep.STATUS_COMPLETE)
        self.step._parameters = {'fake': 'parameters'}
        self.session.add(self.step)
        self.session.commit()
        id = self.step.id

        self.step.reset()
        self.session.commit()

        q_instance = self.session.query(ResourceWorkflowStep).get(id)

        self.assertFalse(q_instance.dirty)
        self.assertEqual(ResourceWorkflowStep.STATUS_PENDING,
                         q_instance.get_status(ResourceWorkflowStep.ROOT_STATUS_KEY))
        self.assertDictEqual({}, q_instance.get_parameters())

    def test_active_roles_constructor(self):
        baseline = ['foo', 'bar']
        instance = ResourceWorkflowStep(name='foo', help='step_0', order=1, active_roles=baseline)
        self.session.add(instance)
        self.session.commit()
        self.assertListEqual(baseline, instance.active_roles)

    def test_active_roles_getter(self):
        baseline = ['foo', 'bar']
        self.step._active_roles = baseline
        ret = self.step.active_roles
        self.assertListEqual(baseline, ret)

    def test_active_roles_setter(self):
        baseline = ['foo', 'bar']
        self.step.active_roles = baseline
        self.assertListEqual(baseline, self.step._active_roles)

    def test_active_roles_setter_not_list(self):
        value_error_raised = False

        try:
            self.step.active_roles = 'not-a-list'
        except ValueError as e:
            value_error_raised = True
            self.assertEqual('Property "active_roles" must be a list of strings. Got "not-a-list" instead.', str(e))
        self.assertTrue(value_error_raised)

    def test_active_roles_setter_not_list_of_strings(self):
        value_error_raised = False

        try:
            self.step.active_roles = [1, 2, 3]
        except ValueError as e:
            value_error_raised = True
            self.assertEqual('Property "active_roles" must be a list of strings. Got "[1, 2, 3]" instead.', str(e))
        self.assertTrue(value_error_raised)
