from unittest.mock import patch, ANY, call, Mock, sentinel

import os
import requests_mock
import shutil
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.test.testcases import TestCase
from django.test.utils import override_settings
from io import BytesIO
from hamcrest import assert_that, contains_inanyorder as contains_in_any_order
from rest_framework.test import APITestCase, APIRequestFactory

from osmaxx import excerptexport
from osmaxx.api_client.conversion_api_client import ConversionApiClient
from osmaxx.conversion_api.statuses import STARTED, QUEUED, FINISHED, FAILED
from osmaxx.excerptexport.models.bounding_geometry import BBoxBoundingGeometry
from osmaxx.excerptexport.models.excerpt import Excerpt
from osmaxx.excerptexport.models.export import Export
from osmaxx.excerptexport.models.extraction_order import ExtractionOrder, ExtractionOrderState
from osmaxx.job_progress import views, middleware


class CallbackHandlingTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.bounding_box = BBoxBoundingGeometry.create_from_bounding_box_coordinates(
            40.77739734768811, 29.528980851173397, 40.77546776498174, 29.525547623634335
        )
        self.excerpt = Excerpt.objects.create(
            name='Neverland', is_active=True, is_public=True, owner=self.user, bounding_geometry=self.bounding_box
        )
        extraction_order = ExtractionOrder.objects.create(
            excerpt=self.excerpt,
            orderer=self.user,
            process_id='53880847-faa9-43eb-ae84-dd92f3803a28',
            extraction_formats=['fgdb', 'spatialite'],
            extraction_configuration={
                'gis_options': {
                    'coordinate_reference_system': 'WGS_84',
                    'detail_level': 1
                }
            },
        )
        self.export = extraction_order.exports.get(file_format='fgdb')
        self.nonexistant_export_id = 999
        self.assertRaises(
            ExtractionOrder.DoesNotExist,
            ExtractionOrder.objects.get, pk=self.nonexistant_export_id
        )

    def test_calling_tracker_with_nonexistant_export_raises_404_not_found(self):
        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.nonexistant_export_id)),
            data=dict(status='http://localhost:8901/api/conversion_result/53880847-faa9-43eb-ae84-dd92f3803a28/')
        )

        self.assertRaises(
            Http404,
            views.tracker, request, export_id=str(self.nonexistant_export_id)
        )
        request.resolver_match

    def test_calling_tracker_with_payload_indicating_queued_updates_export_status(self, *args):
        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='queued', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        self.export.refresh_from_db()
        self.assertEqual(self.export.status, QUEUED)

    def test_calling_tracker_with_payload_indicating_started_updates_export_status(self, *args):
        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='started', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        self.export.refresh_from_db()
        self.assertEqual(self.export.status, STARTED)

    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_queued_informs_user(
            self, emissary_class_mock, *args, **mocks):
        emissary_mock = emissary_class_mock()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='queued', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        assert_that(
            emissary_mock.mock_calls, contains_in_any_order(
                call.info(
                    'Export #{export_id} "Neverland" to ESRI File Geodatabase has been queued.'.format(
                        export_id=self.export.id
                    ),
                ),
            )
        )

    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_started_informs_user(
            self, emissary_class_mock, *args, **mocks):
        emissary_mock = emissary_class_mock()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='started', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        assert_that(
            emissary_mock.mock_calls, contains_in_any_order(
                call.info(
                    'Export #{export_id} "Neverland" to ESRI File Geodatabase has been started.'.format(
                        export_id=self.export.id
                    ),
                ),
            )
        )

    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_failed_informs_user_with_error(
            self, emissary_class_mock, *args, **mocks):
        emissary_mock = emissary_class_mock()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='failed', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        assert_that(
            emissary_mock.mock_calls, contains_in_any_order(
                call.error(
                    'Export #{export_id} "Neverland" to ESRI File Geodatabase has failed.'.format(
                        export_id=self.export.id
                    ),
                ),
            )
        )

    @patch.object(Export, '_fetch_result_file')
    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_finished_informs_user_with_success(
            self, emissary_class_mock, *args, **mocks):
        emissary_mock = emissary_class_mock()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='finished', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        assert_that(
            emissary_mock.mock_calls, contains_in_any_order(
                call.success(
                    'Export #{export_id} "Neverland" to ESRI File Geodatabase has finished.'.format(
                        export_id=self.export.id
                    ),
                ),
            )
        )

    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_unchanged_status_does_not_inform_user(
            self, emissary_class_mock, *args, **mocks):
        self.export.status = 'started'
        self.export.save()
        emissary_mock = emissary_class_mock()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='started', job='http://localhost:8901/api/conversion_job/1/')
        )

        views.tracker(request, export_id=str(self.export.id))
        assert emissary_mock.mock_calls == []

    @patch.object(ConversionApiClient, 'authorized_get', ConversionApiClient.get)  # circumvent authorization logic
    @requests_mock.Mocker(kw='requests')
    def test_calling_tracker_with_payload_indicating_status_finished_downloads_result(self, *args, **mocks):
        self.export.conversion_service_job_id = 1
        self.export.save()

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='finished', job='http://localhost:8901/api/conversion_job/1/')
        )
        requests_mock = mocks['requests']
        requests_mock.get(
            'http://localhost:8901/api/conversion_job/1/',
            json=dict(
                resulting_file='http://localhost:8901/api/conversion_job/1/conversion_result.zip'
            )
        )
        requests_mock.get(
            'http://localhost:8901/api/conversion_job/1/conversion_result.zip',
            body=BytesIO('dummy file'.encode())
        )

        views.tracker(request, export_id=str(self.export.id))
        with self.export.output_file.file as f:
            file_content = f.read()
        assert file_content.decode() == 'dummy file'

    @requests_mock.Mocker(kw='requests')
    @patch.object(ConversionApiClient, 'authorized_get', ConversionApiClient.get)  # circumvent authorization logic
    @patch('osmaxx.utilities.shortcuts.Emissary')
    def test_calling_tracker_with_payload_indicating_final_status_for_only_remaining_nonfinal_export_of_extraction_order_advertises_downloads(
            self, emissary_class_mock, *args, **mocks):
        self.export.conversion_service_job_id = 1
        self.export.save()
        for other_export in self.export.extraction_order.exports.exclude(id=self.export.id):
            other_export.status = FAILED
            other_export.save()
        emissary_mock = emissary_class_mock()
        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(export_id=self.export.id)),
            data=dict(status='finished', job='http://localhost:8901/api/conversion_job/1/')
        )
        requests_mock = mocks['requests']
        requests_mock.get(
            'http://localhost:8901/api/conversion_job/1/',
            json=dict(
                resulting_file='http://localhost:8901/api/conversion_job/1/conversion_result.zip'
            )
        )
        requests_mock.get(
            'http://localhost:8901/api/conversion_job/1/conversion_result.zip',
            body=BytesIO('dummy file'.encode())
        )

        views.tracker(request, export_id=str(self.export.id))

        expected_body = '\n'.join(
            [
                'The extraction order #{order_id} "Neverland" has been processed.',
                'Results available for download:',
                '- ESRI File Geodatabase',  # TODO: download link
                '',
                'The following exports have failed:',
                '- SpatiaLite',
                'Please order them anew if you need them. '
                'If there are repeated failures please inform the administrators.',
                '',
                'View the complete order at http://testserver/orders/{order_id}',
            ]
        ).format(order_id=self.export.extraction_order.id)
        assert_that(
            emissary_mock.mock_calls, contains_in_any_order(
                call.success(
                    'Export #{export_id} "Neverland" to ESRI File Geodatabase has finished.'.format(
                        export_id=self.export.id,
                    ),
                ),
                call.inform_mail(
                    subject='Extraction Order #{order_id} "Neverland": 1 Export finished successfully, 1 failed'.format(
                        order_id=self.export.extraction_order.id,
                    ),
                    mail_body=expected_body,
                ),
            )
        )

    @patch('osmaxx.api_client.conversion_api_client.ConversionApiClient._login')
    @patch.object(ConversionApiClient, 'authorized_get', ConversionApiClient.get)  # circumvent authorization logic
    @patch('osmaxx.api_client.conversion_api_client.ConversionApiClient._download_file')  # mock download
    @requests_mock.Mocker(kw='requests')
    @patch('osmaxx.utilities.shortcuts.Emissary')
    def xtest_calling_tracker_when_status_query_indicates_finished_informs_user(
            self, emissary_class_mock, *args, **mocks
    ):
        emissary_mock = emissary_class_mock()
        requests_mock = mocks['requests']
        requests_mock.get(
            'http://localhost:8901/api/conversion_result/53880847-faa9-43eb-ae84-dd92f3803a28/',
            json={
                "rq_job_id": "53880847-faa9-43eb-ae84-dd92f3803a28",
                "status": "done",
                "progress": "successful",
                "gis_formats": [
                    {
                        "format": "fgdb",
                        "progress": "successful",
                        "result_url": "http://status.example.com"
                    },
                    {
                        "format": "spatialite",
                        "progress": "successful",
                        "result_url": "http://status.example.com"
                    }
                ]
            }
        )

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(order_id=self.extraction_order.id)),
            data=dict(status='http://localhost:8901/api/conversion_result/53880847-faa9-43eb-ae84-dd92f3803a28/')
        )

        views.tracker(request, order_id=str(self.extraction_order.id))
        self.extraction_order.refresh_from_db()
        self.assertEqual(self.extraction_order.state, ExtractionOrderState.FINISHED)
        emissary_mock.success.assert_called_with(
            'The extraction of the order #{} "Neverland" has been finished.'.format(self.extraction_order.id))
        emissary_mock.warn.assert_not_called()
        emissary_mock.error.assert_not_called()

    @patch('osmaxx.api_client.conversion_api_client.ConversionApiClient._login')
    @patch.object(ConversionApiClient, 'authorized_get', ConversionApiClient.get)  # circumvent authorization logic
    @requests_mock.Mocker(kw='requests')
    @patch('osmaxx.utilities.shortcuts.Emissary')
    def xtest_calling_tracker_when_status_query_indicates_error_informs_user(
            self, emissary_class_mock, *args, **mocks
    ):
        emissary_mock = emissary_class_mock()
        requests_mock = mocks['requests']
        requests_mock.get(
            'http://localhost:8901/api/conversion_result/53880847-faa9-43eb-ae84-dd92f3803a28/',
            json={
                "rq_job_id": "53880847-faa9-43eb-ae84-dd92f3803a28",
                "status": "error",
                "progress": "error",
                "gis_formats": [
                    {
                        "format": "fgdb",
                        "progress": "error",
                        "result_url": None
                    },
                    {
                        "format": "spatialite",
                        "progress": "error",
                        "result_url": None
                    }
                ]
            }
        )

        factory = APIRequestFactory()
        request = factory.get(
            reverse('job_progress:tracker', kwargs=dict(order_id=self.extraction_order.id)),
            data=dict(status='http://localhost:8901/api/conversion_result/53880847-faa9-43eb-ae84-dd92f3803a28/')
        )

        views.tracker(request, order_id=str(self.extraction_order.id))
        self.extraction_order.refresh_from_db()
        self.assertEqual(self.extraction_order.state, ExtractionOrderState.FAILED)
        emissary_mock.info.assert_not_called()
        emissary_mock.warn.assert_not_called()
        emissary_mock.error.assert_called_with(
            'The extraction order #{order_id} "Neverland" has failed. Please try again later.'.format(
                order_id=self.extraction_order.id,
            )
        )
        expected_body = '\n'.join(
            [
                'The extraction order #{order_id} "Neverland" could not be completed, please try again later.',
                '',
                'View the order at http://testserver/orders/{order_id}'
            ]
        )
        expected_body = expected_body.format(order_id=self.extraction_order.id)
        emissary_mock.inform_mail.assert_called_with(
            subject='Extraction Order #{order_id} "Neverland" failed'.format(
                order_id=self.extraction_order.id,
            ),
            mail_body=expected_body,
        )

    def tearDown(self):
        if os.path.isdir(settings.PRIVATE_MEDIA_ROOT):
            shutil.rmtree(settings.PRIVATE_MEDIA_ROOT)


class ExportUpdaterMiddlewareTest(TestCase):
    @patch('osmaxx.job_progress.middleware.update_exports_of_request_user')
    def test_request_middleware_updates_exports_of_request_user(self, update_exports_mock):
        self.client.get('/dummy/')
        update_exports_mock.assert_called_once_with(ANY)

    @patch('osmaxx.job_progress.middleware.update_exports_of_request_user')
    def test_request_middleware_passes_request_with_user(self, update_exports_mock):
        self.client.get('/dummy/')
        args, kwargs = update_exports_mock.call_args
        request = args[0]
        self.assertIsNotNone(request.build_absolute_uri.__call__, msg='not a usable request')
        self.assertIsNotNone(request.user)

    @patch('osmaxx.job_progress.middleware.update_exports_of_request_user')
    def test_request_middleware_when_authenticated_passes_request_with_logged_in_user(self, update_exports_mock):
        user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.client.login(username='user', password='pw')
        self.client.get('/dummy/')
        args, kwargs = update_exports_mock.call_args
        request = args[0]
        self.assertIsNotNone(request.build_absolute_uri.__call__, msg='not a usable request')
        self.assertEqual(user, request.user)

    @patch.object(ConversionApiClient, 'authorized_get')
    def test_update_export_set_and_lets_handle_export_status(self, authorized_get_mock):
        authorized_get_mock.return_value.json.return_value = dict(status=sentinel.new_status)
        export_mock = Mock(spec=excerptexport.models.Export())
        export_mock.conversion_service_job_id = 42

        middleware.update_export(export_mock, request=sentinel.REQUEST)

        authorized_get_mock.assert_called_once_with(url='conversion_job/42')
        export_mock.set_and_handle_new_status.assert_called_once_with(
            sentinel.new_status,
            incoming_request=sentinel.REQUEST,
        )


_LOC_MEM_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': __file__,
    }
}


class ExportUpdateTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user('user', 'user@example.com', 'pw')
        other_user = User.objects.create_user('other', 'other@example.com', 'pw')
        own_order = ExtractionOrder.objects.create(orderer=test_user)
        foreign_order = ExtractionOrder.objects.create(orderer=other_user)
        self.own_unfinished_exports = [
            own_order.exports.create(file_format='fgdb') for i in range(2)]
        for i in range(4):
            own_order.exports.create(file_format='fgdb', status=FINISHED)
        for i in range(8):
            own_order.exports.create(file_format='fgdb', status=FAILED)
        for i in range(32):
            foreign_order.exports.create(file_format='fgdb')
        self.client.login(username='user', password='pw')

    @patch('osmaxx.job_progress.middleware.update_export_if_stale')
    def test_update_exports_of_request_user_updates_each_unfinished_export_of_request_user(self, update_progress_mock):
        self.client.get('/dummy/')
        update_progress_mock.assert_has_calls(
            [call(export, request=ANY) for export in self.own_unfinished_exports],
            any_order=True,
        )

    @patch('osmaxx.job_progress.middleware.update_export_if_stale')
    def test_update_exports_of_request_user_does_not_update_any_exports_of_other_users_nor_own_exports_in_a_final_state(
            self, update_progress_mock
    ):
        self.client.get('/dummy/')
        self.assertEqual(update_progress_mock.call_count, len(self.own_unfinished_exports))

    @override_settings(CACHES=_LOC_MEM_CACHE)
    @patch('osmaxx.job_progress.middleware.update_export', return_value="updated")
    def test_update_export_if_stale_when_stale_updates_export(self, update_export_mock):
        assert len(self.own_unfinished_exports) > 1,\
            "Test requires more than one export to prove that exports don't shadow each other in the cache."
        from django.core.cache import cache
        cache.clear()
        for export in self.own_unfinished_exports:
            middleware.update_export_if_stale(export, request=sentinel.REQUEST)
        update_export_mock.assert_has_calls(
            [call(export, request=sentinel.REQUEST) for export in self.own_unfinished_exports],
        )

    @override_settings(CACHES=_LOC_MEM_CACHE)
    @patch('osmaxx.job_progress.middleware.update_export', return_value="updated")
    def test_update_export_if_stale_when_not_stale_does_not_update_export(self, update_export_mock):
        from django.core.cache import cache
        cache.clear()
        the_export = self.own_unfinished_exports[0]
        middleware.update_export_if_stale(the_export, request=Mock())
        middleware.update_export_if_stale(the_export, request=Mock())
        self.assertEqual(update_export_mock.call_count, 1)
