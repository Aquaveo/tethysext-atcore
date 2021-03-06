import json
from tethysext.atcore.models.app_users import AppUser
from tethysext.atcore.mixins.attributes_mixin import AttributesMixin
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ClassWithAttributes(AttributesMixin):
    _attributes = None


class AttributesMixinTests(SqlAlchemyTestCase):

    def setUp(self):
        super().setUp()
        self.instance = ClassWithAttributes()
        self.attributes = {'foo': 'bar', 'num': 1}
        self.attributes_json = json.dumps(self.attributes)

    def tearDown(self):
        del self.instance
        super().tearDown()

    def test_attributes_getter_no_attributes(self):
        val = self.instance.attributes
        self.assertEqual(json.dumps({}), self.instance._attributes)
        self.assertEqual({}, val)

    def test_attributes_getter_with_attributes(self):
        self.instance._attributes = self.attributes_json
        val = self.instance.attributes
        self.assertEqual(self.attributes_json, self.instance._attributes)
        self.assertEqual(self.attributes, val)

    def test_attributes_setter(self):
        self.instance.attributes = self.attributes
        self.assertEqual(self.attributes_json, self.instance._attributes)

    def test_get_attribute_exists(self):
        self.instance._attributes = self.attributes_json
        val_foo = self.instance.get_attribute('foo')
        val_num = self.instance.get_attribute('num')
        self.assertEqual(val_foo, self.attributes['foo'])
        self.assertEqual(val_num, self.attributes['num'])

    def test_get_attribute_not_exists(self):
        val = self.instance.get_attribute('bar')
        self.assertIsNone(val)

    def test_set_attribute(self):
        self.instance.set_attribute('foo', 'bar')
        self.assertIsNotNone(self.instance._attributes)
        _attributes = json.loads(self.instance._attributes)
        self.assertIsInstance(_attributes, dict)
        self.assertIn('foo', _attributes)
        self.assertEqual('bar', _attributes['foo'])

    def test_build_attributes_string(self):
        val = ClassWithAttributes.build_attributes_string(foo='bar', num=1)
        self.assertIsInstance(val, str)
        self.assertGreater(len(val), 0)
        val_dict = json.loads(val)
        self.assertIsInstance(val_dict, dict)
        self.assertEqual(2, len(val_dict))
        self.assertIn('foo', val_dict)
        self.assertEqual('bar', val_dict['foo'])
        self.assertIn('num', val_dict)
        self.assertEqual(1, val_dict['num'])

    def test_build_attributes(self):
        val = ClassWithAttributes.build_attributes(foo='bar', num=1)
        self.assertIsInstance(val, dict)
        self.assertEqual(2, len(val))
        self.assertIn('foo', val)
        self.assertEqual('bar', val['foo'])
        self.assertIn('num', val)
        self.assertEqual(1, val['num'])

    def test_build_attributes_app_users_model(self):
        app_user = AppUser(
            username='lskywalker',
            role=AppUser.ROLES.ORG_USER
        )
        self.session.add(app_user)
        self.session.commit()

        val = ClassWithAttributes.build_attributes(user=app_user)
        self.assertIsInstance(val, dict)
        self.assertEqual(1, len(val))
        self.assertIn('user', val)
        self.assertEqual(str(app_user.id), val['user'])
