import json
from unittest import mock
from .copying_mock import CopyingMock
from requests.models import Response
from collections import OrderedDict

from django.contrib.auth.models import User
from django.test.testcases import TestCase

from osmaxx.excerptexport.services import ConversionApiClient
from osmaxx.excerptexport.models import Excerpt, ExtractionOrder, ExtractionOrderState, BBoxBoundingGeometry


class ConversionApiClientTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.bounding_box = BBoxBoundingGeometry.create_from_bounding_box_coordinates(
            40.77739734768811, 29.528980851173397, 40.77546776498174, 29.525547623634335
        )
        self.excerpt = Excerpt.objects.create(
            name='Neverland', is_active=True, is_public=True, owner=self.user, bounding_geometry=self.bounding_box
        )
        self.extraction_order = ExtractionOrder.objects.create(excerpt=self.excerpt, orderer=self.user)
        self.extraction_order.extraction_configuration = {
            'gis': {
                'formats': ['fgdb', 'spatialite'],
                'options': {
                    'coordinate_reference_system': 'WGS_84',
                    'detail_level': 1
                }
            }
        }

    def _create_response(self, status_code=200, reason='OK', headers={'content-type': 'application/json'}, json={}):
        response = Response()
        response.status_code = status_code
        response.reason = reason
        response.headers = headers
        response.json = CopyingMock(return_value=json)
        return response

    def test_successful_login(self):
        response = self._create_response(
            status_code=200,
            reason='OK',
            json={'token': 'abcdefgh12345678'}
        )
        response_mock_factory = CopyingMock(return_value=response)

        with mock.patch('requests.post', new=response_mock_factory) as request_post_mock:
            api_client = ConversionApiClient(
                'http', 'www.osmaxx.ch', '8000',
                {'login': '/api/token-auth/?format=json'},
                {'username': 'osmaxxi', 'password': '12345678'}
            )
            self.assertFalse(api_client.is_logged_in)

            success = api_client.login()

            request_post_mock.assert_called_with(
                'http://www.osmaxx.ch:8000/api/token-auth/?format=json',
                data=json.dumps({'username': 'osmaxxi', 'password': '12345678'}),
                headers={'Content-Type': 'application/json; charset=UTF-8'}
            )

            self.assertTrue(success)
            self.assertTrue(api_client.is_logged_in)
            self.assertEqual(api_client.headers['Authorization'], 'JWT abcdefgh12345678')

    def test_failed_login(self):
        response = self._create_response(
            status_code=400,
            reason='BAD REQUEST',
            json={'non_field_errors': ['Unable to login with provided credentials.']}
        )
        response_mock_factory = CopyingMock(return_value=response)

        with mock.patch('requests.post', new=response_mock_factory) as request_post_mock:
            api_client = ConversionApiClient(
                'http', 'www.osmaxx.ch', '8000',
                {'login': '/api/token-auth/?format=json'},
                {'username': 'osmaxxi', 'password': 'wrong-password'}
            )
            self.assertFalse(api_client.is_logged_in)

            success = api_client.login()

            request_post_mock.assert_called_with(
                'http://www.osmaxx.ch:8000/api/token-auth/?format=json',
                data=json.dumps({'username': 'osmaxxi', 'password': 'wrong-password'}),
                headers={'Content-Type': 'application/json; charset=UTF-8'}
            )

            self.assertFalse(success)
            self.assertFalse(api_client.is_logged_in)
            self.assertFalse('Authorization' in api_client.headers)

    def test_create_job(self):
        response = self._create_response(json=OrderedDict({
            "id": 5,
            "rq_job_id": "81cca3a9-5e66-47ab-8d3f-70739e4204ae",
            "callback_url": "http://example.com",
            "status": "http://localhost:9000/api/conversion_result/81cca3a9-5e66-47ab-8d3f-70739e4204ae/",
            "gis_formats": [
                "fgdb",
                "spatialite"
            ],
            "gis_options": {
                "coordinate_reference_system": "WGS_84",
                "detail_level": 1
            },
            "extent": {
                "id": 5,
                "west": 29.525547623634335,
                "south": 40.77546776498174,
                "east": 29.528980851173397,
                "north": 40.77739734768811,
                "polyfile": None
            }
        }))
        response_mock_factory = CopyingMock(return_value=response)

        with mock.patch('requests.post', new=response_mock_factory) as request_post_mock:
            api_client = ConversionApiClient(
                'http', 'www.osmaxx.ch', '8000',
                {'job': {'create': '/api/jobs'}},
                {'username': 'osmaxxi', 'password': '12345678'}
            )
            api_client.is_logged_in = True
            api_client.headers['Authorization'] = 'JWT abcdefgh12345678'

            success = api_client.create_job(self.extraction_order)

            request_post_mock.assert_called_with(
                'http://www.osmaxx.ch:8000/api/jobs',
                data=json.dumps(OrderedDict({
                    "callback_url": "http://example.com",
                    "gis_formats": ["fgdb", "spatialite"],
                    "gis_options": {
                        "coordinate_reference_system": "WGS_84",
                        "detail_level": 1
                    },
                    "extent": {
                        "west": 29.525547623634335,
                        "south": 40.77546776498174,
                        "east": 29.528980851173397,
                        "north": 40.77739734768811,
                        "polyfile": None
                    }
                })),
                headers=OrderedDict({
                    'Content-Type': 'application/json; charset=UTF-8',
                    'Authorization': 'JWT abcdefgh12345678'
                })
            )

            self.assertTrue(success)
            self.assertEqual(self.extraction_order.state, ExtractionOrderState.PROCESSING)
            self.assertEqual(self.extraction_order.process_id, '81cca3a9-5e66-47ab-8d3f-70739e4204ae')

    def _status_side_effect(self, url, data={}, headers={}):
        response = Response()
        response.status_code = 200
        response.reason = 'OK'

        if '/api/conversion_result/4b529c79-559c-4730-9cd2-03ea91c9a5ef' in url:
            response.headers = {'content-type': 'application/json'}
            response.json = CopyingMock(return_value=OrderedDict({
                "rq_job_id": "4b529c79-559c-4730-9cd2-03ea91c9a5ef",
                "status": "done",
                "progress": "successful",
                "gis_formats": [
                    {
                        "format": "fgdb",
                        "progress": "successful",
                        "result_url": "http://localhost:8000/api/gis_format/11/download_result/"
                    },
                    {
                        "format": "spatialite",
                        "progress": "successful",
                        "result_url": "http://localhost:8000/api/gis_format/12/download_result/"
                    }
                ]
            }))
        elif '/api/gis_format/11/download_result/' in url:
            response.headers = OrderedDict({
                'content-type': 'text/html; charset=utf-8',
                'content-disposition': 'attachment; filename="osmaxx_excerpt_2015-11-11_155844_fgdb.zip"'
            })
            response._content = b'PK\x03\x04\n\x00\x00\x00\x00\xa9\x00\xa9\x00~X\x00\x00\xf0\x8b\x06\x00\x00\x00'

        elif '/api/gis_format/12/download_result/' in url:
            response.headers = OrderedDict({
                'content-type': 'text/html; charset=utf-8',
                'content-disposition': 'attachment; filename="osmaxx_excerpt_2015-11-11_155845_fgdb.zip"'
            })
            response._content = b'PK\x03\x03\n\x00\x06\x00\x00\xa9\x00\xb9\x00~X\x00\x00\xd0\x8b\x06\x00'

        return response

    def test_download_files(self):
        response_mock_factory = CopyingMock(side_effect=self._status_side_effect)
        with mock.patch('requests.get', new=response_mock_factory) as request_get_mock:
            api_client = ConversionApiClient(
                'http', 'www.osmaxx.ch', '8000',
                {'job': {'status': '/api/conversion_result/{rq_job_id}'}},
                {'username': 'osmaxxi', 'password': '12345678'}
            )
            api_client.is_logged_in = True
            api_client.headers['Authorization'] = 'JWT abcdefgh12345678'
            self.extraction_order.process_id = '4b529c79-559c-4730-9cd2-03ea91c9a5ef'

            success = api_client.download_result_files(self.extraction_order)

            self.assertEqual(request_get_mock.call_count, 3)
            request_get_mock.assert_any_call(
                'http://www.osmaxx.ch:8000/api/conversion_result/4b529c79-559c-4730-9cd2-03ea91c9a5ef',
                headers={'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'JWT abcdefgh12345678'}
            )
            request_get_mock.assert_any_call(
                'http://localhost:8000/api/gis_format/11/download_result/',
                headers={'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'JWT abcdefgh12345678'}
            )
            request_get_mock.assert_any_call(
                'http://localhost:8000/api/gis_format/12/download_result/',
                headers={'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'JWT abcdefgh12345678'}
            )
            self.assertTrue(success)
            self.assertEqual(self.extraction_order.output_files.count(), 2)
            self.assertEqual(self.extraction_order.output_files.order_by('id')[0].content_type, 'fgdb')
            self.assertEqual(self.extraction_order.output_files.order_by('id')[1].content_type, 'spatialite')
            self.assertEqual(
                self.extraction_order.output_files.order_by('id')[0].file.read(),
                b'PK\x03\x04\n\x00\x00\x00\x00\xa9\x00\xa9\x00~X\x00\x00\xf0\x8b\x06\x00\x00\x00'
            )
            self.assertEqual(
                self.extraction_order.output_files.order_by('id')[1].file.read(),
                b'PK\x03\x03\n\x00\x06\x00\x00\xa9\x00\xb9\x00~X\x00\x00\xd0\x8b\x06\x00'
            )

    def test_order_status_processing(self):
        job_status_mock_factory = CopyingMock(return_value=OrderedDict({
            "rq_job_id": "4b529c79-559c-4730-9cd2-03ea91c9a5ef",
            "status": "started",
            "progress": "started",
            "gis_formats": [
                {
                    "format": "fgdb",
                    "progress": "started",
                    "result_url": None
                },
                {
                    "format": "spatialite",
                    "progress": "started",
                    "result_url": None
                }
            ]
        }))
        with mock.patch(
            'osmaxx.excerptexport.services.ConversionApiClient.job_status',
            new=job_status_mock_factory
        ) as job_status_mock:
            api_client = ConversionApiClient(
                'http', 'www.osmaxx.ch', '8000',
                {'job': {'status': '/api/conversion_result/{rq_job_id}'}},
                {'username': 'osmaxxi', 'password': '12345678'}
            )
            api_client.is_logged_in = True
            api_client.headers['Authorization'] = 'JWT abcdefgh12345678'
            self.extraction_order.process_id = '4b529c79-559c-4730-9cd2-03ea91c9a5ef'

            self.assertEqual(self.extraction_order.output_files.count(), 0)
            self.assertNotEqual(self.extraction_order.state, ExtractionOrderState.PROCESSING)

            api_client.update_order_status(self.extraction_order)
            job_status_mock.assert_called_with(self.extraction_order)
            self.assertEqual(self.extraction_order.state, ExtractionOrderState.PROCESSING)
            self.assertEqual(self.extraction_order.output_files.count(), 0)

    def test_order_status_done(self):
        job_status_mock_factory = CopyingMock(return_value=OrderedDict({
            "rq_job_id": "4b529c79-559c-4730-9cd2-03ea91c9a5ef",
            "status": "done",
            "progress": "successful",
            "gis_formats": [
                {
                    "format": "fgdb",
                    "progress": "successful",
                    "result_url": "http://localhost:8000/api/gis_format/11/download_result/"
                },
                {
                    "format": "spatialite",
                    "progress": "successful",
                    "result_url": "http://localhost:8000/api/gis_format/12/download_result/"
                }
            ]
        }))
        with mock.patch('osmaxx.excerptexport.services.ConversionApiClient.job_status', new=job_status_mock_factory):
            download_file_mock_factory = CopyingMock(return_value=True)
            with mock.patch(
                'osmaxx.excerptexport.services.ConversionApiClient.download_result_files',
                new=download_file_mock_factory
            ) as download_file_mock:
                api_client = ConversionApiClient(
                    'http', 'www.osmaxx.ch', '8000',
                    {'job': {'status': '/api/conversion_result/{rq_job_id}'}},
                    {'username': 'osmaxxi', 'password': '12345678'}
                )
                api_client.is_logged_in = True
                api_client.headers['Authorization'] = 'JWT abcdefgh12345678'
                self.extraction_order.process_id = '4b529c79-559c-4730-9cd2-03ea91c9a5ef'
                self.extraction_order.state = ExtractionOrderState.PROCESSING

                self.assertEqual(self.extraction_order.output_files.count(), 0)
                self.assertNotEqual(self.extraction_order.state, ExtractionOrderState.FINISHED)

                api_client.update_order_status(self.extraction_order)
                download_file_mock.assert_called_with(self.extraction_order)
                self.assertEqual(self.extraction_order.state, ExtractionOrderState.FINISHED)
