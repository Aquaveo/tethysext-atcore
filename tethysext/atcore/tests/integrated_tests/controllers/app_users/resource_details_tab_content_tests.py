"""
********************************************************************************
* Name: resource_details_tab_content_tests.py
* Author: nswain
* Created On: July 31, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from unittest import mock
import unittest
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from tethysext.atcore.tests.factories.django_user import UserFactory
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow
from tethysext.atcore.controllers.app_users.resource_details_tab_content import ResourceDetailsTabContent


class FakeResourceDetailsTabContent(ResourceDetailsTabContent):
    """
    Controller for resource_details page.

    GET: Render detail view of given resource.
    """
    template_name = None
    base_template = 'fake/base.html'
    http_method_names = ['get']
    resource_workflows = {
        'Fake Workflow': mock.MagicMock
    }
    test_preview_image_url = ''

    def get_resource_map_manager(self):
        return mock.MagicMock()

    def get_model_spatial_manager(self):
        return mock.MagicMock()

    def preview_image(self, request, context):
        return "Map Preview", self.test_preview_image_url

    def get_summary_tab_info(self, request, resource):
        summary_columns = [
            [
                ('General Parameters', {'A': 'B'})
            ],
            [
                ('Grid Parameters', {'A': 'B'}),
                ('Time Parameters', {'A': 'B'}),
                ('Output Parameters', {'A': 'B'})
            ],
            [
                ('Output Files', {'A': 'B'})
            ]
        ]
        return summary_columns


class ResourceDetailsTabContentTests(unittest.TestCase):

    def setUp(self):
        self.ggmdtc_controller = FakeResourceDetailsTabContent()
        self.ggmdtc_controller._app = mock.MagicMock()
        self.request_factory = RequestFactory()
        self.resource_id = '624ceaca-22dd-42fd-9f9d-7517844514b8'
        self.mock_workflow = mock.MagicMock(
            spec=ResourceWorkflow,
            STATUS_ERROR='Error',
            STATUS_WORKING='Working',
            STATUS_COMPLETE='Complete',
            STATUS_PENDING='Pending',
            STATUS_FAILED='Failed'
        )

    def tearDown(self):
        pass

    def assert_workflow_card_is_valid(self, workflow_card):
        self.assertIn('id', workflow_card)
        self.assertIn('name', workflow_card)
        self.assertIn('type', workflow_card)
        self.assertIn('creator', workflow_card)
        self.assertIn('date_created', workflow_card)
        self.assertIn('resource', workflow_card)
        self.assertIn('status', workflow_card)
        self.assertIn('can_delete', workflow_card)
        self.assertIn('title', workflow_card['status'])
        self.assertIn('style', workflow_card['status'])
        self.assertIn('href', workflow_card['status'])

    @mock.patch('tethys_apps.decorators.has_permission')
    def test__handle_get__summary(self, _):
        self.ggmdtc_controller._handle_summary_tab = mock.MagicMock()
        self.ggmdtc_controller.get_resource = mock.MagicMock()
        self.ggmdtc_controller._app = mock.MagicMock()

        request = self.request_factory.get(
            '/apps/fake/' + self.resource_id + '/get-tab/summary/'
        )

        request.user = UserFactory()

        response = self.ggmdtc_controller._handle_get(
            request=request,
            resource_id=self.resource_id,
            tab='summary'
        )

        context = {
            'resource': self.ggmdtc_controller.get_resource(),
            'back_url': self.ggmdtc_controller.back_url

        }

        self.ggmdtc_controller._handle_summary_tab.assert_called_with(request, self.resource_id, context)
        self.assertEqual(self.ggmdtc_controller._handle_summary_tab(), response)

    @mock.patch('tethys_apps.decorators.has_permission')
    def test__handle_get__summary_preview_image(self, _):
        self.ggmdtc_controller._handle_summary_tab_preview_image = mock.MagicMock()
        self.ggmdtc_controller._get_back_controller = mock.MagicMock()
        self.ggmdtc_controller.get_resource = mock.MagicMock()
        self.ggmdtc_controller._app = mock.MagicMock()

        request = self.request_factory.get(
            '/apps/fake/' + self.resource_id + '/get-tab/summary-preview-image/'
        )

        request.user = UserFactory()

        response = self.ggmdtc_controller._handle_get(
            request=request,
            resource_id=self.resource_id,
            tab='summary-preview-image'
        )

        context = {
            'resource': self.ggmdtc_controller.get_resource(),
            'back_url': self.ggmdtc_controller.back_url

        }

        self.ggmdtc_controller._handle_summary_tab_preview_image.assert_called_with(request, self.resource_id, context)
        self.assertEqual(self.ggmdtc_controller._handle_summary_tab_preview_image(), response)

    @mock.patch('tethys_apps.decorators.has_permission')
    def test__handle_get__workflows(self, _):
        self.ggmdtc_controller._handle_workflows_tab = mock.MagicMock()
        self.ggmdtc_controller._get_back_controller = mock.MagicMock()
        self.ggmdtc_controller.get_resource = mock.MagicMock()
        self.ggmdtc_controller._app = mock.MagicMock()

        request = self.request_factory.get(
            '/apps/fake/' + self.resource_id + '/get-tab/workflows/'
        )

        request.user = UserFactory()

        response = self.ggmdtc_controller._handle_get(
            request=request,
            resource_id=self.resource_id,
            tab='workflows'
        )

        context = {
            'resource': self.ggmdtc_controller.get_resource(),
            'back_url': self.ggmdtc_controller.back_url

        }

        self.ggmdtc_controller._handle_workflows_tab.assert_called_with(request, self.resource_id, context)
        self.assertEqual(self.ggmdtc_controller._handle_workflows_tab(), response)

    @mock.patch('tethys_apps.decorators.has_permission')
    def test__handle_get__invalid_tab(self, _):
        self.ggmdtc_controller._get_back_controller = mock.MagicMock()
        self.ggmdtc_controller._get_resource = mock.MagicMock()
        self.ggmdtc_controller._app = mock.MagicMock()

        request = self.request_factory.get(
            '/apps/fake/' + self.resource_id + '/get-tab/invalid/'
        )

        request.user = UserFactory()

        response = self.ggmdtc_controller._handle_get(
            request=request,
            resource_id=self.resource_id,
            tab='invalid'
        )

        self.assertEqual(404, response.status_code)
        self.assertIn(b'"invalid" is not a valid tab.', response.content)

    @mock.patch('tethys_apps.decorators.has_permission')
    def test__handle_get__get_resource_redirect(self, _):
        mock_redirect = mock.MagicMock(spec=HttpResponseRedirect)
        self.ggmdtc_controller.get_resource = mock.MagicMock(return_value=mock_redirect)
        self.ggmdtc_controller._app = mock.MagicMock()

        request = self.request_factory.get(
            '/apps/fake/' + self.resource_id + '/get-tab/invalid/'
        )

        request.user = UserFactory()

        response = self.ggmdtc_controller._handle_get(
            request=request,
            resource_id=self.resource_id,
            tab='workflows'
        )

        self.assertEqual(mock_redirect, response)

    def test__handle_summary_tab(self):
        pass
        # TODO: Write this test

    def test__handle_summary_tab_locked_all_users(self):
        pass
        # TODO: Write this test

    def test__handle_summary_tab_locked_for_one_user(self):
        pass
        # TODO: Write this test

    def test__handle_summary_tab_preview_image(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_error_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_working_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_complete_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_failed_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_pending_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_approved_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_rejected_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_submitted_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_changed_requested_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_under_review_status(self):
        pass
        # TODO: Write this test

    def test__handle_workflow_tab_null_status(self):
        pass
        # TODO: Write this test
