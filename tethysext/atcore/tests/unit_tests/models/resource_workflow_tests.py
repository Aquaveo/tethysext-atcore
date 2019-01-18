import datetime as dt
import unittest
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.models.app_users import AppUsersBase, ResourceWorkflow, AppUser, Resource

from tethysext.atcore.tests import TEST_DB_URL


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class ResourceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.transaction = connection.begin_nested()
        self.session = Session(connection)

        self.name = "test_workflow"
        self.pre_created_date = dt.datetime.utcnow()

        self.user = AppUser(
            username="user1",
            role=Roles.ORG_USER,
        )

        self.session.add(self.user)

        self.resource = Resource(
            name='eggs',
            description='for eating',
        )

        self.session.add(self.resource)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_create_resource_workflow(self):
        resource_workflow = ResourceWorkflow(
            name=self.name,
            creator=self.user,
            resource=self.resource
        )

        self.session.add(resource_workflow)
        self.session.commit()

        all_resources_count = self.session.query(ResourceWorkflow).count()
        all_resources = self.session.query(ResourceWorkflow).all()

        self.assertEqual(all_resources_count, 1)
        for resource_workflow in all_resources:
            self.assertEqual(self.name, resource_workflow.name)
            self.assertEqual(ResourceWorkflow.TYPE, resource_workflow.type)
            self.assertGreater(resource_workflow.date_created, self.pre_created_date)
            self.assertEqual(self.resource, resource_workflow.resource)
            self.assertEqual(self.user, resource_workflow.creator)

    # TODO: Need to finish the following test
    def test_next_step(self):
        resource_workflow = ResourceWorkflow(
            name=self.name,
            creator=self.user,
            resource=self.resource
        )

        self.session.add(resource_workflow)
        self.session.commit()
        # ret = resource_workflow.get_next_step()
        pass
