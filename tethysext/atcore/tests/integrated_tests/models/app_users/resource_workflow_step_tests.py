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
        self.instance = ResourceWorkflowStep(name='foo', help='step_0', order=1)
        self.session.add(self.instance)

        self.workflow.steps = [self.instance]
        self.session.add(self.workflow)
        self.session.commit()

    def test__repr__(self):
        blank_baseline = '<ResourceWorkflowStep name="{}" id="{}" >'.format(self.instance.name, self.instance.id)
        self.assertEqual(blank_baseline, repr(self.instance))

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_to_dict(self, mock_init_params):
        # Test the abstract base class is empty by default
        baseline = {'parameters': {}}
        self.assertDictEqual(baseline, self.instance.to_dict())

        mock_init_params.side_effect = [{
            'test_not_required_parameter': {
                'help': 'test parameter not required help.',
                'value': None,
                'required': False
            }}]
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1, child_id='None')
        baseline = {
            'type': 'generic_workflow_step',
            'name': 'bar',
            'help': 'step_1',
            'child_id': 'None',
            'parameters': {
                'test_not_required_parameter': None
            }
        }
        self.assertDictEqual(baseline, self.instance.to_dict())

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_to_json(self, mock_init_params):
        # Test the abstract base class is empty by default
        baseline = json.dumps({'parameters': {}})
        self.assertEqual(baseline, self.instance.to_json())

        mock_init_params.side_effect = [{
            'test_not_required_parameter': {
                'help': 'test parameter not required help.',
                'value': None,
                'required': False
            }}]
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        baseline = json.dumps({
            'type': 'generic_workflow_step',
            'name': 'bar',
            'help': 'step_1',
            'parameters': {
                "test_not_required_parameter": None}
        })

        self.assertEqual(baseline, self.instance.to_json())

    def test_validate_valid(self):
        # Ensure the empty class is valid
        self.assertIsNone(self.instance.validate())

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
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.assertRaises(ValueError, self.instance.validate)

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
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.instance.parse_parameters(params)
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
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)

        self.instance.set_parameter(name='param_1', value=True)
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
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.assertRaises(ValueError, self.instance.set_parameter, name='param_not_found', value=True)

    def test_get_parameter_param_not_found_empty_class(self):
        # Test the blank class
        self.assertRaises(ValueError, self.instance.get_parameter, 'foo')

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
        self.instance = ResourceWorkflowStep(name='bar', help='step_1', order=1)
        self.instance.set_parameter('param_1', True)
        self.assertTrue(self.instance.get_parameter('param_1'))

    def test_get_parameters(self):
        baseline = {}
        self.instance._parameter = baseline
        self.assertTrue(baseline is not self.instance.get_parameters())

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option(self, mock_options):
        parent = ResourceWorkflowStep(name='baz', help='step_2', order=2)
        self.instance = ResourceWorkflowStep(name='foo', help='step_0', order=1, parent=parent)
        mock_options.get.return_value = {'parent': 'test_data'}
        magic_parent = mock.MagicMock()
        magic_parent.get_parameter.return_value = 'Test'
        self.instance.parent = magic_parent
        ret = self.instance.resolve_option('option')
        magic_parent.get_parameter.assert_called_with('test_data')
        self.assertEqual('Test', ret)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option_no_option_value(self, mock_options):
        mock_options.get.return_value = None
        self.assertIsNone(self.instance.resolve_option('option'))
        mock_options.get.assert_called_with('option', None)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.options')
    def test_resolve_option_ValueError(self, mock_options):
        parent = ResourceWorkflowStep(name='baz', help='step_2', order=2)
        self.instance = ResourceWorkflowStep(name='foo', help='step_0', order=1, parent=parent)
        mock_options.get.return_value = {'parent': 'test_data'}
        magic_parent = mock.MagicMock()
        magic_parent.get_parameter.side_effect = [ValueError]
        self.instance.parent = magic_parent
        self.assertRaises(RuntimeError, self.instance.resolve_option, 'option')
        magic_parent.get_parameter.assert_called_with('test_data')

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow_step.ResourceWorkflowStep.init_parameters')
    def test_reset(self, mock_init_parameters):
        mock_init_parameters.return_value = {}
        self.instance = ResourceWorkflowStep(name='foo', help='step_0', order=1, dirty=True)
        self.instance.set_status(ResourceWorkflowStep.ROOT_STATUS_KEY, ResourceWorkflowStep.STATUS_COMPLETE)
        self.instance._parameters = {'fake': 'parameters'}
        self.session.add(self.instance)
        self.session.commit()
        id = self.instance.id

        self.instance.reset()
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
        self.instance._active_roles = baseline
        ret = self.instance.active_roles
        self.assertListEqual(baseline, ret)

    def test_active_roles_setter(self):
        baseline = ['foo', 'bar']
        self.instance.active_roles = baseline
        self.assertListEqual(baseline, self.instance._active_roles)

    def test_active_roles_setter_not_list(self):
        value_error_raised = False

        try:
            self.instance.active_roles = 'not-a-list'
        except ValueError as e:
            value_error_raised = True
            self.assertEqual('Property "active_roles" must be a list of strings. Got "not-a-list" instead.', str(e))
        self.assertTrue(value_error_raised)

    def test_active_roles_setter_not_list_of_strings(self):
        value_error_raised = False

        try:
            self.instance.active_roles = [1, 2, 3]
        except ValueError as e:
            value_error_raised = True
            self.assertEqual('Property "active_roles" must be a list of strings. Got "[1, 2, 3]" instead.', str(e))
        self.assertTrue(value_error_raised)
