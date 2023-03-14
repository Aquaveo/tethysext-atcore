"""
********************************************************************************
* Name: resource_workflows_tests.py
* Author: mlebaron
* Created On: September 4, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from unittest import mock
import unittest
from tethysext.atcore.tests.mock.url_map_maker import MockUrlMapMaker
from tethysext.atcore.urls.resource_workflows import urls
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.controllers.resource_workflows.resource_workflow_router import ResourceWorkflowRouter
from tethysext.atcore.models.app_users.app_user import AppUser
from tethysext.atcore.models.app_users.organization import Organization
from tethysext.atcore.models.app_users.resource import Resource
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


class RandomSubclass:
    pass


class ValidPermissionsChild(AppPermissionsManager):
    pass


class AppUserChild(AppUser):
    pass


class OrganizationChild(Organization):
    TYPE = 'testing__organization_child__testing'
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }


class ResourceChild(Resource):
    TYPE = 'testing__resource_child__testing'
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': TYPE
    }


class ResourceWorkflowsTests(unittest.TestCase):

    def setUp(self):
        self.app = mock.MagicMock()
        self.persistent_store_name = 'some_store_name'
        self.workflow_pairs = [(ResourceWorkflow, ResourceWorkflowRouter)]
        self.base_url_name = 'foo/bar'
        self.custom_models = [AppUserChild, OrganizationChild, ResourceChild]

        self.generic_urls = [
            'resources/{resource_id}/generic_workflow/{workflow_id}',
            'resources/{resource_id}/generic_workflow/{workflow_id}/step/{step_id}',
            'resources/{resource_id}/generic_workflow/{workflow_id}/step/{step_id}/result/{result_id}'
        ]

    def tearDown(self):
        pass

    def verify_url_maps(self, url_maps, urls, use_parent_classes=True, use_permissions_parent=True):
        app_user_class = AppUser if use_parent_classes else AppUserChild
        organization_class = Organization if use_parent_classes else OrganizationChild
        resource_class = Resource if use_parent_classes else ResourceChild
        permissions_class = AppPermissionsManager if use_permissions_parent else ValidPermissionsChild

        self.assertEqual(3, len(url_maps))

        workflow_map = url_maps[0].controller.__dict__['view_initkwargs']
        self.assertEqual('generic_workflow_workflow', url_maps[0].name)
        self.assertEqual(urls[0], url_maps[0].url)
        self.assertEqual(self.app, workflow_map['_app'])
        self.assertEqual(self.persistent_store_name, workflow_map['_persistent_store_name'])
        self.assertIs(workflow_map['_AppUser'], app_user_class)
        self.assertIs(workflow_map['_Organization'], organization_class)
        self.assertIs(workflow_map['_Resource'], resource_class)
        self.assertIs(workflow_map['_PermissionsManager'], permissions_class)
        self.assertIs(workflow_map['_ResourceWorkflow'], ResourceWorkflow)

        step_map = url_maps[1].controller.__dict__['view_initkwargs']
        self.assertEqual('generic_workflow_workflow_step', url_maps[1].name)
        self.assertEqual(urls[1], url_maps[1].url)
        self.assertEqual(self.app, step_map['_app'])
        self.assertEqual(self.persistent_store_name, step_map['_persistent_store_name'])
        self.assertIs(step_map['_AppUser'], app_user_class)
        self.assertIs(step_map['_Organization'], organization_class)
        self.assertIs(step_map['_Resource'], resource_class)
        self.assertIs(step_map['_PermissionsManager'], permissions_class)
        self.assertIs(step_map['_ResourceWorkflow'], ResourceWorkflow)

        result_map = url_maps[2].controller.__dict__['view_initkwargs']
        self.assertEqual('generic_workflow_workflow_step_result', url_maps[2].name)
        self.assertEqual(urls[2], url_maps[2].url)
        self.assertEqual(self.app, result_map['_app'])
        self.assertEqual(self.persistent_store_name, result_map['_persistent_store_name'])
        self.assertIs(result_map['_AppUser'], app_user_class)
        self.assertIs(result_map['_Organization'], organization_class)
        self.assertIs(result_map['_Resource'], resource_class)
        self.assertIs(result_map['_PermissionsManager'], permissions_class)
        self.assertIs(result_map['_ResourceWorkflow'], ResourceWorkflow)

    def test_urls_invalid_custom_model(self):
        try:
            urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs,
                 custom_models=[RandomSubclass()])
            self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('custom_models must contain only subclasses of AppUser, Resources, or Organization.',
                             str(e))

    def test_urls_with_custom_model(self):
        url_maps = urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs,
                        custom_models=self.custom_models)

        use_parent_classes = False
        self.verify_url_maps(url_maps, self.generic_urls, use_parent_classes=use_parent_classes)

    def test_urls_invalid_custom_permissions_manager(self):
        try:
            urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs,
                 custom_permissions_manager=RandomSubclass())
            self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('custom_permissions_manager must be a subclass of AppPermissionsManager.', str(e))

    def test_urls_with_custom_permissions_manager(self):
        url_maps = urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs,
                        custom_permissions_manager=ValidPermissionsChild)

        use_permissions_parent = False
        self.verify_url_maps(url_maps, self.generic_urls, use_permissions_parent=use_permissions_parent)

    def test_urls_with_base_url_path(self):
        url_maps = urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs,
                        base_url_path='/my/path/')

        expected_urls = [
            'my/path/resources/{resource_id}/generic_workflow/{workflow_id}',
            'my/path/resources/{resource_id}/generic_workflow/{workflow_id}/step/{step_id}',
            'my/path/resources/{resource_id}/generic_workflow/{workflow_id}/step/{step_id}/result/{result_id}'
        ]
        self.verify_url_maps(url_maps, expected_urls)

    def test_urls_no_optional_params(self):
        url_maps = urls(MockUrlMapMaker, self.app, self.persistent_store_name, self.workflow_pairs)

        self.verify_url_maps(url_maps, self.generic_urls)

    def test_urls_no_workflow_pairs(self):
        url_maps = urls(MockUrlMapMaker, self.app, self.persistent_store_name, [])

        self.assertEqual(0, len(url_maps))

    def test_urls_invalid_resource_workflow(self):
        workflow_pairs = [(None, ResourceWorkflowRouter)]

        try:
            urls(MockUrlMapMaker, self.app, self.persistent_store_name, workflow_pairs)
            self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('Must provide a valid ResourceWorkflow model as the first item in the '
                             'workflow_pairs argument.', str(e))

    def test_urls_invalid_resource_workflow_router(self):
        workflow_pairs = [(ResourceWorkflow, None)]

        try:
            urls(MockUrlMapMaker, self.app, self.persistent_store_name, workflow_pairs)
            self.assertTrue(False)  # This line should not be hit
        except ValueError as e:
            self.assertEqual('Must provide a valid ResourceWorkflowRouter controller as the second item in the '
                             'workflow_pairs argument.', str(e))
