import datetime
import uuid
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import SqlAlchemyTestCase
from tethysext.atcore.tests.utilities.sqlalchemy_helpers import setup_module_for_sqlalchemy_tests, \
    tear_down_module_for_sqlalchemy_tests


def setUpModule():
    setup_module_for_sqlalchemy_tests()


def tearDownModule():
    tear_down_module_for_sqlalchemy_tests()


class ResourceTests(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.name = "A Resource"
        self.description = "Bad Description"
        self.status = "Processing"
        self.creation_date = datetime.datetime.utcnow()

    def test_create_resource(self):
        resource = Resource(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date,
        )

        self.session.add(resource)
        self.session.commit()

        all_resources_count = self.session.query(Resource).count()
        all_resources = self.session.query(Resource).all()

        self.assertEqual(all_resources_count, 1)
        for resource in all_resources:
            self.assertEqual(resource.name, self.name)
            self.assertEqual(resource.description, self.description)
            self.assertEqual(resource.date_created, self.creation_date)
            self.assertEqual(resource.status, self.status)
            self.assertFalse(resource.public)
            self.assertEqual(resource.type, Resource.TYPE)
            self.assertIsInstance(resource.id, uuid.UUID)

    def test_resource__repr__(self):
        resource = Resource(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date,
        )
        self.session.add(resource)
        self.session.commit()

        ret = resource.__repr__()

        self.assertEqual(f'<Resource name="A Resource" id="{resource.id}" locked=False>', ret)

    def test_resource_SLUG(self):
        class TestSlug(Resource):
            DISPLAY_TYPE_PLURAL = 'Test Resources'

        resource = TestSlug(
            name=self.name,
            description=self.description,
            status=self.status,
            date_created=self.creation_date,
        )

        self.session.add(resource)
        self.session.commit()

        ret = resource.SLUG

        self.assertEqual(ret, 'test_resources')
