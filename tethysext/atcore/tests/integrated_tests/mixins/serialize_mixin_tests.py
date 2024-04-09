import json
import uuid
import datetime as dt
from unittest import mock
from tethysext.atcore.models.app_users import Organization, Resource, ResourceWorkflow
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS, ResultsResourceWorkflowStep
from tethysext.atcore.models.resource_workflow_results import SpatialWorkflowResult
from tethysext.atcore.services.map_manager import MapManagerBase
from tethysext.atcore.services.base_spatial_manager import BaseSpatialManager
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class CustomWorkflow(ResourceWorkflow):
    TYPE = 'testing__custom_resource_workflow_serialization__testing'
    DISPLAY_TYPE_SINGULAR = 'Custom Serialization Workflow'
    DISPLAY_TYPE_PLURAL = 'Custom Serialization Workflows'

    __mapper_args__ = {'polymorphic_identity': TYPE}

    some_field = 'bar'
    some_date = dt.datetime(2024, 4, 8)
    some_id = uuid.uuid4()

    @classmethod
    def new(cls, app, name, resource_id, creator_id, geoserver_name, map_manager, spatial_manager, **kwargs):
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id, lock_when_finished=False)
        test_step = SpatialInputRWS(
            name='Test Spatial Input Step',
            order=10,
            help="This is just for testing step serialization.",
            options={
                'shapes': ['points'],
                'singular_name': 'Point',
                'plural_name': 'Points',
                'allow_shapefile': True,
                'allow_drawing': True,
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
        )
        workflow.steps.append(test_step)
        test_result_step = ResultsResourceWorkflowStep(
            name='Test Review Results',
            order=30,
            help='This is just for testing results serialization.',
        )
        workflow.steps.append(test_result_step)

        test_map_result = SpatialWorkflowResult(
            name='Test Map Result',
            codename='generic_map',
            description='This is just for testing map results serialization.',
            order=10,
            options={
                'layer_group_title': 'Points',
                'layer_group_control': 'checkbox'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager
        )

        test_result_step.results.append(test_map_result)

        return workflow

    def get_url_name(self):
        return 'custom_workflow'

    def serialize_custom_fields(self, d: dict):
        d.update(
            {
                'some_field': self.some_field,
                'some_date': self.some_date,
                'some_id': self.some_id,
            }
        )
        return d


class CustomResource(Resource):
    TYPE = 'testing__custom_resource_serialization__testing'
    DISPLAY_TYPE_SINGULAR = 'Custom Serialization Resource'
    DISPLAY_TYPE_PLURAL = 'Custom Serialization Resources'
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }
    some_field = 'bar'
    some_date = dt.datetime(2024, 4, 8)
    some_id = uuid.uuid4()

    def serialize_custom_fields(self, d: dict):
        d.update(
            {
                'some_field': self.some_field,
                'some_date': self.some_date,
                'some_id': self.some_id,
            }
        )
        return d


class SerializeMixinResourceTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.organization = Organization(
            name='Test Serialization Oranzation',
            active=True,
            license=Organization.LICENSES.STANDARD,
        )

        self.resource = CustomResource(
            name='Test Serialization Resource',
            description='A test resource',
            created_by='test_user',
        )
        self.resource.set_status(Resource.STATUS_AVAILABLE)
        self.resource.set_attribute('some_attr', 'baz')
        self.resource.organizations.append(self.organization)
        self.session.add(self.resource)
        self.session.commit()

    def tearDown(self):
        super().tearDown()

    def verify_resource_fields(self, d, format='dict'):
        if format == 'json':
            d = json.loads(d)

        # Verify base fields
        if format == 'json':
            self.assertEqual(d['id'], str(self.resource.id))
        else:
            self.assertEqual(d['id'], self.resource.id)
        self.assertEqual(d['name'], self.resource.name)
        self.assertEqual(d['type'], self.resource.type)
        self.assertEqual(d['locked'], self.resource.is_user_locked)
        self.assertEqual(d['status'], self.resource.get_status())
        self.assertDictEqual(d['attributes'], self.resource.attributes)

        # Verify Resource fields
        if format == 'json':
            self.assertEqual(d['date_created'], self.resource.date_created.isoformat())
        else:
            self.assertEqual(d['date_created'], self.resource.date_created)
        self.assertEqual(d['description'], self.resource.description)
        self.assertEqual(d['display_type_plural'], self.resource.DISPLAY_TYPE_PLURAL)
        self.assertEqual(d['display_type_singular'], self.resource.DISPLAY_TYPE_SINGULAR)
        self.assertEqual(d['slug'], self.resource.SLUG)
        self.assertFalse(d['public'])
        self.assertEqual(len(d['organizations']), 1)
        org_dict = {
            'id': self.organization.id,
            'name': 'Test Serialization Oranzation'
        }
        if format == 'json':
            org_dict['id'] = str(self.organization.id)
        self.assertDictEqual(d['organizations'][0], org_dict)

        # Verify custom fields
        self.assertEqual(d['some_field'], self.resource.some_field)
        if format == 'json':
            self.assertEqual(d['some_date'], self.resource.some_date.isoformat())
            self.assertEqual(d['some_id'], str(self.resource.some_id))
        else:
            self.assertEqual(d['some_date'], self.resource.some_date)
            self.assertEqual(d['some_id'], self.resource.some_id)

    def test_resource_serialize_dict(self):
        s_dict = self.resource.serialize()
        self.assertIsInstance(s_dict, dict)
        self.verify_resource_fields(s_dict, format='dict')

    def test_resource_serialize_json(self):
        s_json = self.resource.serialize(format='json')
        self.assertIsInstance(s_json, str)
        self.verify_resource_fields(s_json, format='json')

    def test_resource_serialize_invalid_format(self):
        with self.assertRaises(ValueError):
            self.resource.serialize(format='invalid_format')


class SerializeMixinResourceWorkflowTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.app_user = self.get_user(return_app_user=True)
        self.resource = CustomResource(
            name='Test Serialization Resource',
            description='A test resource',
            created_by='test_user'
        )
        self.session.add(self.resource)
        self.session.commit()

        self.workflow = CustomWorkflow.new(
            app='some_app',
            name='Test Serialization Workflow',
            resource_id=self.resource.id,
            creator_id=self.app_user.id,
            geoserver_name='foo_geoserver',
            map_manager=MapManagerBase,
            spatial_manager=BaseSpatialManager,
        )
        self.workflow.set_attribute('some_attr', 'baz')
        self.session.add(self.workflow)
        self.session.commit()

        self.workflow_url = '/some/url/to/a/custom-workflow/'

    def tearDown(self):
        super().tearDown()

    def verify_resource_workflow_fields(self, d, format='dict'):
        if format == 'json':
            d = json.loads(d)

        # Verify base fields
        if format == 'json':
            self.assertEqual(d['id'], str(self.workflow.id))
        else:
            self.assertEqual(d['id'], self.workflow.id)
        self.assertEqual(d['name'], self.workflow.name)
        self.assertEqual(d['type'], self.workflow.type)
        self.assertEqual(d['locked'], self.workflow.is_user_locked)
        self.assertEqual(d['status'], self.workflow.get_status())
        self.assertDictEqual(d['attributes'], self.workflow.attributes)

        # Verify Resource Workflow fields
        self.assertEqual(d['created_by'], self.workflow.creator.username)
        if format == 'json':
            self.assertEqual(d['date_created'], self.workflow.date_created.isoformat())
        else:
            self.assertEqual(d['date_created'], self.workflow.date_created)
        self.assertEqual(d['display_type_plural'], self.workflow.DISPLAY_TYPE_PLURAL)
        self.assertEqual(d['display_type_singular'], self.workflow.DISPLAY_TYPE_SINGULAR)
        self.assertEqual(d['url'], self.workflow_url)

        # Verify steps
        self.assertEqual(len(d['steps']), 2)
        self.assertDictEqual(d['steps'][0], {
            'help': 'This is just for testing step serialization.',
            'id': str(self.workflow.steps[0].id),
            'name': 'Test Spatial Input Step',
            'parameters': {'geometry': None, 'imagery': None},
            'resource_workflow_id': str(self.workflow.id),
            'type': 'spatial_input_workflow_step'
        })
        self.assertDictEqual(d['steps'][1], {
            'help': 'This is just for testing results serialization.',
            'id': str(self.workflow.steps[1].id),
            'name': 'Test Review Results',
            'parameters': {},
            'resource_workflow_id': str(self.workflow.id),
            'type': 'results_resource_workflow_step'
        })

        # Verify results
        self.assertEqual(len(d['results']), 1)
        result_dict = {
            'attributes': {},
            'codename': 'generic_map',
            'data': {},
            'id': self.workflow.steps[1].results[0].id,
            'name': 'Test Map Result',
            'order': 10,
            'status': None,
            'type': 'spatial_workflow_result'
        }
        if format == 'json':
            result_dict['id'] = str(self.workflow.steps[1].results[0].id)
        self.assertDictEqual(d['results'][0], result_dict)

        # Verify custom fields
        self.assertEqual(d['some_field'], self.workflow.some_field)
        if format == 'json':
            self.assertEqual(d['some_date'], self.workflow.some_date.isoformat())
            self.assertEqual(d['some_id'], str(self.workflow.some_id))
        else:
            self.assertEqual(d['some_date'], self.workflow.some_date)
            self.assertEqual(d['some_id'], self.workflow.some_id)

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.reverse')
    def test_resource_workflow_serialize_dict(self, mock_reverse):
        mock_reverse.return_value = self.workflow_url
        s_dict = self.workflow.serialize()
        self.assertIsInstance(s_dict, dict)
        self.verify_resource_workflow_fields(s_dict, format='dict')
        mock_reverse.assert_called_with(
            'custom_workflow', kwargs={'resource_id': self.resource.id, 'workflow_id': self.workflow.id}
        )

    @mock.patch('tethysext.atcore.models.app_users.resource_workflow.reverse')
    def test_resource_workflow_serialize_json(self, mock_reverse):
        mock_reverse.return_value = self.workflow_url
        s_json = self.workflow.serialize(format='json')
        self.assertIsInstance(s_json, str)
        self.verify_resource_workflow_fields(s_json, format='json')
        mock_reverse.assert_called_with(
            'custom_workflow', kwargs={'resource_id': self.resource.id, 'workflow_id': self.workflow.id}
        )

    def test_resource_workflow_serialize_invalid_format(self):
        with self.assertRaises(ValueError):
            self.workflow.serialize(format='invalid_format')
