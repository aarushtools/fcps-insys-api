import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fcps_insys_api.config import API, APP, load_config
from fcps_insys_api.utils.main import InsysAPI, InsysAPIException


class TestInsysAPI(unittest.TestCase):
    def test_get_course_list(self):
        course_list = InsysAPI(location_id=503).get_course_list()
        self.assertIn("data", course_list)

    def test_get_course_detailed_info(self):
        course_info = InsysAPI(location_id=503).get_course_detailed_info(course_id=17380)
        self.assertTrue(course_info["data"]["course"]["description"].startswith("Students study AI"))

    def test_course_list_to_simple(self):
        insys_api = InsysAPI(location_id=503)
        insys_api.course_list_to_simple(insys_api.get_course_list())

    def test_convert_requisites_to_ids(self):
        insys_api = InsysAPI(location_id=503)
        reqs = insys_api.convert_requisites_to_id(
            "Artificial Intel 1 & (Artificial Intel 2)",
            insys_api.course_list_to_simple(insys_api.get_course_list()),
        )
        course_id = insys_api.course_list_to_simple(insys_api.get_course_list())["Artificial Intel 1 TJ AV"]
        self.assertEqual(reqs[0], course_id)

    @patch("fcps_insys_api.utils.main.urllib.request.urlopen")
    def test_wrong_endpoint_request(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 201
        mock_response.read.return_value = b'{"message": "Resource created"}'

        mock_urlopen.return_value.__enter__.return_value = mock_response

        insys_api = InsysAPI(location_id=503)
        with self.assertRaises(InsysAPIException):
            insys_api.get_course_list()

    def test_get_default_endpoint(self):
        self.assertEqual(InsysAPI.get_default_endpoint(), API.ENDPOINT)


class TestConfig(unittest.TestCase):
    def test_config(self):
        load_config(None)
        self.assertFalse(APP.PRODUCTION)
        self.assertEqual(API.URL, "/api")

        load_config(str(Path("test_config.py").absolute()))
        self.assertTrue(APP.PRODUCTION)
        self.assertEqual(API.URL, "/testapi")
