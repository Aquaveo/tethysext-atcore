import json
import uuid
import datetime as dt
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class CustomResource(Resource):
    TYPE = 'custom_resource'
    DISPLAY_TYPE_SINGULAR = 'Custom'
    DISPLAY_TYPE_PLURAL = 'Customs'
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


class SerializeMixinTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.instance = Resource(
            name='Test Resource',
            description='A test resource',
            created_by='test_user',
        )
        self.instance.set_status(Resource.STATUS_AVAILABLE)
        self.instance.set_attribute('some_attr', 'baz')

    def tearDown(self):
        super().tearDown()

    def verify_resource_fields(self, d, format='dict'):
        if format == 'json':
            d = json.loads(d)

        # Verify base fields
        self.assertEqual(d['id'], self.instance.id)
        if format == 'json':
            self.assertEqual(d['date_created'], self.instance.date_created.isoformat())
        else:
            self.assertEqual(d['date_created'], self.instance.date_created)
        self.assertEqual(d['name'], self.instance.name)
        self.assertEqual(d['type'], self.instance.type)

        # Verify Resource fields
        self.assertEqual(d['description'], self.instance.description)
        self.assertEqual(d['locked'], self.instance.is_user_locked)
        self.assertEqual(d['status'], self.instance.get_status())
        self.assertDictEqual(d['attributes'], self.instance.attributes)
        self.assertEqual(d['display_type_plural'], self.instance.DISPLAY_TYPE_PLURAL)
        self.assertEqual(d['display_type_singular'], self.instance.DISPLAY_TYPE_SINGULAR)
        self.assertEqual(d['slug'], self.instance.SLUG)

        # Verify custom fields
        self.assertEqual(d['some_field'], self.instance.some_field)
        if format == 'json':
            self.assertEqual(d['some_date'], self.instance.some_date.isoformat())
        else:
            self.assertEqual(d['some_date'], self.instance.some_date)
        if format == 'json':
            self.assertEqual(d['some_id'], str(self.instance.some_id))
        else:
            self.assertEqual(d['some_id'], self.instance.some_id)

    def test_resource_serialize_dict(self):
        s_dict = self.instance.serialize()
        self.assertIsInstance(s_dict, dict)
        self.verify_resource_fields(s_dict, format='dict')

    def test_resource_serialize_json(self):
        s_json = self.instance.serialize(format='json')
        self.assertIsInstance(s_json, str)
        self.verify_resource_fields(s_json, format='json')

    def test_resource_serialize_invalid_format(self):
        with self.assertRaises(ValueError):
            self.instance.serialize(format='invalid_format')
