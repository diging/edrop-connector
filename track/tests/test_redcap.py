# test_redcap.py

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings

from track.models import Order
from track.redcap import (
    get_record_info,
    set_order_number,
    set_tracking_info
)


# Override the REDCAP_URL setting to use a test URL instead of the real one
# This ensures we don't make actual HTTP requests to REDCap during testing
@override_settings(REDCAP_URL="http://testurl")
class TestRedcapFunctions(TestCase):

    def setUp(self):
        # Common test data
        self.record_id = "123"
        self.order_number = "ORD-456"
        self.mock_record_data = [{
            "record_id": "123",
            "first_name": "John",
            "last_name": "Doe",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704",
            "street_1": "742 Evergreen Terrace",
            "street_2": "",
            "consent_complete": "2",
            "contact_complete": "2"
        }]

        # Create an Order in the DB for shipping tests
        self.order_for_shipping = Order.objects.create(
            project_id="ABC123",
            record_id=self.record_id,
            order_status=Order.INITIATED,
            ship_date="2025-02-14",
            tracking_nrs=["1Z12345", "1Z67890"],
            return_tracking_nrs=["999999"],
            tube_serials=["TUBE-001", "TUBE-002"]
        )

    @patch("track.redcap.requests.post")
    def test_get_record_info_success(self, mock_post):
        """
        Test get_record_info returns a dict when the request is successful (HTTP 200).
        """
        # Configure the mock response for a successful POST request.
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_record_data
        mock_post.return_value = mock_response

        result = get_record_info(self.record_id)

        # Verify the function returns the expected data.
        self.assertIsNotNone(result)
        self.assertEqual(result["record_id"], "123")
        self.assertEqual(result["first_name"], "John")
        self.assertEqual(result["last_name"], "Doe")

        # Inspect the positional arguments of the POST call.
        args, kwargs = mock_post.call_args
        # The first positional argument should be the URL.
        self.assertEqual(args[0], settings.REDCAP_URL)
        # The POST call should include data parameter.
        self.assertIn("data", kwargs)
        self.assertIn("records[0]", kwargs["data"])
        self.assertEqual(kwargs["data"]["records[0]"], self.record_id)

    @patch("track.redcap.requests.post")
    def test_get_record_info_failure(self, mock_post):
        """
        Test get_record_info returns None if the response is not HTTP 200.
        """
        # Configure a failed response.
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        mock_post.return_value = mock_response

        result = get_record_info(self.record_id)
        self.assertIsNone(result)

    @patch("track.redcap.requests.post")
    def test_set_order_number_success(self, mock_post):
        """
        Test set_order_number logs success on a 200 response.
        """
        # Configure a successful response.
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 1}
        mock_post.return_value = mock_response

        set_order_number(self.record_id, self.order_number)

        # Verify that the POST call was made with the correct dummy URL.
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], settings.REDCAP_URL)
        self.assertIn("data", kwargs)

        # The XML payload should contain the record_id and kit_order_n.
        xml_payload = kwargs["data"]["data"]
        self.assertIn(f"<record_id>{self.record_id}</record_id>", xml_payload)
        self.assertIn(f"<kit_order_n>{self.order_number}</kit_order_n>", xml_payload)

    @patch("track.redcap.requests.post")
    def test_set_order_number_failure(self, mock_post):
        """
        Test set_order_number logs error on a non-200 response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad Request"}
        mock_post.return_value = mock_response

        set_order_number(self.record_id, self.order_number)
        mock_post.assert_called_once()

    @patch("track.redcap.requests.post")
    def test_set_tracking_info_success(self, mock_post):
        """
        Test set_tracking_info builds correct XML and sends to REDCap.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 1}
        mock_post.return_value = mock_response

        # Use only orders with a ship_date.
        orders = Order.objects.filter(ship_date__isnull=False)
        set_tracking_info(orders)

        # Verify the POST call.
        args, kwargs = mock_post.call_args
        xml_payload = kwargs["data"]["data"]

        # Check that the XML payload includes the correct order details.
        self.assertIn(f"<record_id>{self.record_id}</record_id>", xml_payload)
        self.assertIn("<kit_tracking_n>1Z12345, 1Z67890</kit_tracking_n>", xml_payload)
        self.assertIn("<kit_tracking_return_n>999999</kit_tracking_return_n>", xml_payload)
        self.assertIn("<tubeserial>TUBE-001, TUBE-002</tubeserial>", xml_payload)
        self.assertIn("<kit_status>TRN</kit_status>", xml_payload)

    @patch("track.redcap.requests.post")
    def test_set_tracking_info_no_orders(self, mock_post):
        """
        Test set_tracking_info does nothing if no shipped orders are provided.
        """
        # Passing an empty list should result in no HTTP request.
        set_tracking_info([])
        mock_post.assert_not_called()

    @patch("track.redcap.requests.post")
    def test_set_tracking_info_failure(self, mock_post):
        """
        Test set_tracking_info logs errors on a non-200 response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad Request"}
        mock_post.return_value = mock_response

        orders = Order.objects.filter(ship_date__isnull=False)
        set_tracking_info(orders)
        mock_post.assert_called_once()