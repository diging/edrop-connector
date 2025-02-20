import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
import json

import track.gbf as gbf
from track.models import *

logger = logging.getLogger(__name__)

order_json = {
    "test": "true",
    "orders": [
        {
            "orderNumber": "EDROP-00014",
            "shippingInfo": {
                "address": {
                    "company": "John Doe",
                    "addressLine1": "1234 Main Street",
                    "addressLine2": "PO Box 5",
                    "city": "Phoenix",
                    "state": "AZ",
                    "zipCode": "00000",
                    "country": "United States",
                    "phone": "1111111111",
                    "residential": True
                },
                "shipMethod": "FedEx Ground",
            },
            "lineItems": [
                {
                "itemNumber": "111",
                "itemQuantity": 1.0,
                }
            ]
        }
    ]
}

address_data = {
    "first_name": "John",
    "last_name": "Doe",
    "street1": "1234 Main Street",
    "street2": "PO Box 5",
    "city": "Phoenix",
    "state": "AZ",
    "zip": "00000",
    "phone": "1111111111",
}

class OrderResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self.json_data = json_data

    def json(self):
        return self.json_data

confirmation_response_json = {
    "success": True,
    "dataArray": [
        {
            "format": "json",
            "data": "{\r\n  \"ShippingConfirmations\": [\r\n    {\r\n      \"OrderNumber\": \"EDROP-00014\",\r\n      \"Shipper\": \"\",\r\n      \"ShipVia\": \"FedEx Ground\",\r\n      \"ShipDate\": \"2025-01-23\",\r\n      \"ClientID\": \"\",\r\n      \"Tracking\": [\r\n        \"270000004830\"\r\n      ],\r\n      \"Items\": [\r\n        {\r\n          \"ItemNumber\": \"K-BAN-001\",\r\n          \"SerialNumber\": \"EV-05FCSG\",\r\n          \"ShippedQty\": 1,\r\n          \"ReturnTracking\": [\r\n            \"XXXXXXXXXXXX\"\r\n          ],\r\n          \"TubeSerial\": [\r\n            \"SIHIRJT5786\"\r\n          ]\r\n        }\r\n      ]\r\n    }\r\n  ]\r\n}"
        }
    ]
}

tracking_info = {
    'EDROP-00014': {
        'date_kit_shipped': '2025-01-23',
        'kit_tracking_n': ['270000004830'],
        'return_tracking_n': ['XXXXXXXXXXXX'],
        'tube_serial_n': ['SIHIRJT5786']
    }
}

@override_settings(GBF_URL="http://host.docker.internal:3000/")
class TestGBF(TestCase):
    def setUp(self):
        self.mock_order_number = "EDROP-00014"
        self.mock_order_json = order_json
        self.mock_order_response = OrderResponse(200, {'success': True, 'message': 'EXM-0000XX_RDQYD_20250115_154237.xml'})
        self.order_object = Order.objects.create(pk=14, project_id=1, order_number=None)
        self.address_data = address_data
        self.order_response_json = {'success': True, 'message': 'EXM-0000XX_RDQYD_20250115_154237.xml'}
        self.order_numbers =  ["EDROP-00014", "EDROP-00015"]
        self.confirmation_response_json = confirmation_response_json
        self.tracking_info = tracking_info

    @patch("track.gbf._place_order_with_GBF")
    @patch("track.gbf._generate_order_json")
    @patch("track.gbf._generate_order_number")
    def test_create_order(self, mock_generate_order_number, mock_generate_order_json, mock_place_order_with_GBF):
        mock_generate_order_number.return_value = self.mock_order_number
        mock_generate_order_json.return_value = self.mock_order_json
        mock_place_order_with_GBF.side_effect = lambda json, order_number: self.mock_order_response

        result = gbf.create_order(self.order_object, self.address_data)

        updated_order_object = Order.objects.filter(pk=self.order_object.id).first()
        
        self.assertEqual(updated_order_object.order_number, "EDROP-00014")
        self.assertEqual(result, True)

        logger.debug(f'Order {updated_order_object.order_number} was successfully created.')

    def test_generate_order_number(self):
        result = gbf._generate_order_number(self.order_object)
        self.assertEqual(result, "EDROP-00014")

    def test_generate_order_json(self):
        self.order_object.order_number = "EDROP-00014"

        result = gbf._generate_order_json(self.order_object, self.address_data)
        result_data = json.loads(result)

        self.assertIn("test", result_data)
        self.assertIn("orders", result_data)
        self.assertIn("orderNumber", result_data['orders'][0])
        self.assertIn("shippingInfo", result_data['orders'][0])
        self.assertIn("lineItems", result_data['orders'][0])
        self.assertIn("address", result_data['orders'][0]['shippingInfo'])
        self.assertIn("shipMethod", result_data['orders'][0]['shippingInfo'])
        self.assertEqual(result_data['orders'][0]['orderNumber'], "EDROP-00014")
        self.assertEqual(result_data['orders'][0]['shippingInfo']['address']['company'], "John Doe")
        self.assertEqual(result_data['orders'][0]['shippingInfo']['address']['zipCode'], "00000")

    @patch("track.gbf.requests.post")
    def test_place_order_with_GBF_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.order_response_json
        mock_request.return_value = mock_response
        
        result = gbf._place_order_with_GBF(self.mock_order_json, self.mock_order_number)
        result_body = result.json()

        mock_request.assert_called_once()
        self.assertEqual(result.status_code, 200)
        self.assertIn("success", result_body)
        self.assertIn("message", result_body)
        self.assertEqual(result_body["success"], True)

        logger.debug(f'Order {self.mock_order_json['orders'][0]['orderNumber']} was successfully placed.')

    @patch("track.gbf.requests.post")
    def test_place_order_with_GBF_failure(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"success": False, "error": "Bad Request"}
        mock_request.return_value = mock_response
        
        result = gbf._place_order_with_GBF(self.mock_order_json, self.mock_order_number)

        mock_request.assert_called_once()
        self.assertEqual(result.status_code, 400)

        logger.error('The order was unable to be placed due to a bad request.')

    @patch("track.gbf._extract_tracking_info")
    @patch("track.gbf.requests.post")
    def test_get_order_confirmations_success(self, mock_request, mock_extract_tracking_info):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.confirmation_response_json
        mock_request.return_value = mock_response
        mock_extract_tracking_info.return_value = self.tracking_info

        result = gbf.get_order_confirmations(self.order_numbers)

        mock_request.assert_called_once()
        mock_extract_tracking_info.assert_called_once()
        self.assertIn("EDROP-00014", result)
        self.assertIn("2025-01-23", result['EDROP-00014']['date_kit_shipped'])
        self.assertIn("270000004830", result['EDROP-00014']['kit_tracking_n'])
        self.assertIn('XXXXXXXXXXXX', result['EDROP-00014']['return_tracking_n'])
        self.assertIn('SIHIRJT5786', result['EDROP-00014']['tube_serial_n'])

        logger.debug(f'The following order numbers were successfully checked for order confirmation: {self.order_numbers}')

    @patch("track.gbf.requests.post")
    def test_get_order_confirmations_failure(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"success": False, "error": "Bad Request"}
        mock_request.return_value = mock_response
        
        result = gbf.get_order_confirmations(self.order_numbers)

        mock_request.assert_called_once()
        self.assertEqual(result, None)

        logger.error('The order confirmation failed due to a bad request.')
