import unittest
from unittest.mock import patch, MagicMock
import httpx
import os

# Set environment variable for testing
os.environ["RAPIDAPI_KEY"] = "dummy_key"
os.environ["RAPIDAPI_HOST"] = "linkedin-data-api.p.rapidapi.com"

from main import search_locations, search_jobs, get_job_details

class TestLinkedInMCP(unittest.TestCase):

    @patch('main.httpx.Client')
    def test_search_locations_success(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "urn:li:geo:106187582",
                        "name": "India"
                    }
                ]
            }
        }
        mock_client.get.return_value = mock_response

        # Act
        result = search_locations("India")

        # Assert
        self.assertEqual(result, "106187582")
        mock_client.get.assert_called_once_with(
            "https://linkedin-data-api.p.rapidapi.com/search-locations?keyword=India"
        )

    @patch('main.httpx.Client')
    def test_search_locations_api_error(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "This service is no longer available at this location. Please contact support@professionalnetworkdata.com"
        }
        mock_client.get.return_value = mock_response

        # Act
        result = search_locations("India")

        # Assert
        self.assertIn("API Error:", result)
        self.assertIn("support@professionalnetworkdata.com", result)

    @patch('main.httpx.Client')
    def test_search_locations_network_exception(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError("Connection failed")

        # Act
        result = search_locations("India")

        # Assert
        self.assertIn("Error searching locations:", result)

    @patch('main.search_locations')
    @patch('main.httpx.Client')
    def test_search_jobs_success(self, mock_client_class, mock_search_locations):
        # Arrange
        mock_search_locations.return_value = "106187582"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": [
                {
                    "id": "123456",
                    "title": "Software Engineer fresher",
                    "company": {
                        "name": "Tech Corp",
                        "logo": "logo.png"
                    },
                    "location": "Bengaluru, India",
                    "url": "https://linkedin.com/jobs/view/123456",
                    "postAt": "2026-08-20"
                }
            ]
        }
        mock_client.get.return_value = mock_response

        # Act
        result = search_jobs("fresher B.Tech", limit=1, location="India", format_output=False)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["jobs"][0]["title"], "Software Engineer fresher")
        self.assertEqual(result["jobs"][0]["company"], "Tech Corp")
        self.assertEqual(result["jobs"][0]["id"], "123456")

    @patch('main.search_locations')
    @patch('main.httpx.Client')
    def test_search_jobs_api_error(self, mock_client_class, mock_search_locations):
        # Arrange
        mock_search_locations.return_value = "106187582"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "This service is no longer available at this location."
        }
        mock_client.get.return_value = mock_response

        # Act
        result = search_jobs("fresher B.Tech", limit=1, location="India", format_output=False)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("This service is no longer available", result["error"])

    @patch('main.httpx.Client')
    def test_get_job_details_success(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "123456",
                "title": "Software Engineer fresher",
                "description": "Must have B.Tech in Computer Science or IT."
            }
        }
        mock_client.get.return_value = mock_response

        # Act
        result = get_job_details("123456")

        # Assert
        self.assertEqual(result["title"], "Software Engineer fresher")
        self.assertEqual(result["description"], "Must have B.Tech in Computer Science or IT.")
        mock_client.get.assert_called_once_with(
            "https://linkedin-data-api.p.rapidapi.com/get-job-details?id=123456"
        )

class TestLinkedInJobSearchAPI(unittest.TestCase):

    def setUp(self):
        # Swap host to the newer one
        self.original_host = os.environ.get("RAPIDAPI_HOST")
        os.environ["RAPIDAPI_HOST"] = "linkedin-job-search-api.p.rapidapi.com"

    def tearDown(self):
        if self.original_host:
            os.environ["RAPIDAPI_HOST"] = self.original_host
        else:
            del os.environ["RAPIDAPI_HOST"]

    def test_search_locations_fantastic_jobs(self):
        # In main.py, search_locations returns keyword directly for this host
        result = search_locations("India")
        self.assertEqual(result, "India")

    @patch('main.httpx.Client')
    def test_search_jobs_fantastic_jobs_success(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 123456789,
                "title": "Software Developer fresher",
                "organization": "Innovate Ltd",
                "org_logo_permalink": "logo.png",
                "location": "Mumbai, India",
                "url": "https://linkedin.com/jobs/view/123456789",
                "posted_at": "2026-08-22T00:00:00Z"
            }
        ]
        mock_client.get.return_value = mock_response

        # Act
        result = search_jobs("fresher", limit=1, location="India", format_output=False)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["jobs"][0]["title"], "Software Developer fresher")
        self.assertEqual(result["jobs"][0]["company"], "Innovate Ltd")
        self.assertEqual(result["jobs"][0]["id"], "123456789")

    @patch('main.httpx.Client')
    def test_get_job_details_fantastic_jobs(self, mock_client_class):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123456789,
            "title": "Software Developer fresher",
            "description": "Full description here"
        }
        mock_client.get.return_value = mock_response

        # Act
        result = get_job_details("123456789")

        # Assert
        self.assertEqual(result["id"], 123456789)
        self.assertEqual(result["description"], "Full description here")
        mock_client.get.assert_called_once_with(
            "https://linkedin-job-search-api.p.rapidapi.com/job/detail?job_id=123456789"
        )

if __name__ == '__main__':
    unittest.main()

