# import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
import json, requests
from http import HTTPStatus

import track.gbf as gbf
from track.models import *

order_json = {
    "test": "true",
    "orders": [
        {
            "orderNumber": 1,
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

class TestsGBF(TestCase):
    def setUp(self):
        self.order_object = Order.objects.create(pk=24, project_id=1, order_number=2)
        self.order_json = order_json
        self.address_data = address_data

    # @patch("track.gbf._generate_order_number")
    def test_generate_order_number(self, mock_obj):
        # mock_obj.return_value = "EDROP-%05d"%(self.order_object.pk)
        result = gbf._generate_order_number(self.order_object)

        self.assertEqual(result, "EDROP-00024")
        # mock_obj.assert_called_once()

    # @patch("track.gbf._generate_order_json")
    def test_generate_order_json(self, mock_obj):
        # mock_obj.return_value = json.dumps(self.order_json)
        result = gbf._generate_order_json(self.order_object, self.address_data)
        result_data = json.loads(result)

        self.assertIn("test", result_data)
        self.assertIn("orders", result_data)
        self.assertIn("orderNumber", result_data['orders'][0])
        self.assertIn("shippingInfo", result_data['orders'][0])
        self.assertIn("lineItems", result_data['orders'][0])
        self.assertIn("address", result_data['orders'][0]['shippingInfo'])
        self.assertIn("shipMethod", result_data['orders'][0]['shippingInfo'])
        self.assertEqual(result_data['orders'][0]['orderNumber'], 1)
        self.assertEqual(result_data['orders'][0]['shippingInfo']['address']['company'], "John Doe")
        self.assertEqual(result_data['orders'][0]['shippingInfo']['address']['zipCode'], "00000")
        # mock_obj.assert_called_once()

    # @patch("track.gbf.requests.post")
    def test_place_order_with_GBF_post_request(self, mock_obj):
        headers = {
            'Authorization': 'Bearer XXX',
            'Content-Type': 'application/json'
        }
        url = "http://host.docker.internal:3000/oap/api/order"
        response = requests.post(url, data=self.order_json, headers=headers)
        self.assertEqual(response.json.status_code, HTTPStatus.OK)
        self.assertIn("success", response.json())
        # mock_obj.json.return_value = {}

        # gbf._place_order_with_GBF(order_json)
    
    # To-Do:Test the confirmations flow to get the exact response of the post request
    # and then mock it
    @patch("track.gbf.requests.post")
    def test_check_order_response(self, mock_response):
        mock_response = MagicMock()
        mock_response.status_code() = 201
        mock_response.json.return_value = {}
        result = gbf._check_order_response(response)
        mock_response.assert_called_once()
        self.assertEqual(result, True)

    def test_get_order_confirmations(self):
        order_numbers = [1, 2, 3, 4]
        headers = {
            'Authorization': 'Bearer XXX',
            'Content-Type': 'application/json'
        }
        content = {'orderNumbers': order_numbers, 'format': 'json'}
        url = "http://host.docker.internal:3000/oap/api/confirm2"
        response = requests.post(url, data=content, headers=headers)
        response_json = response.json()

        self.assertEqual(response.json.status_code, HTTPStatus.OK)
        self.assertIn("success", response_json)
        self.assertIn("dataArray", response_json)
        self.assertIn("format", response_json['dataArray'])
        self.assertIn("data", response_json['dataArray'])

    def test_extract_tracking_info(self):
        data = "{\r\n  \"ShippingConfirmations\": [\r\n    {\r\n      \"OrderNumber\": \"EDROP-00014\",\r\n      \"Shipper\": \"\",\r\n      \"ShipVia\": \"FedEx Ground\",\r\n      \"ShipDate\": \"2025-01-23\",\r\n      \"ClientID\": \"\",\r\n      \"Tracking\": [\r\n        \"270000004830\"\r\n      ],\r\n      \"Items\": [\r\n        {\r\n          \"ItemNumber\": \"K-BAN-001\",\r\n          \"SerialNumber\": \"EV-05FCSG\",\r\n          \"ShippedQty\": 1,\r\n          \"ReturnTracking\": [\r\n            \"XXXXXXXXXXXX\"\r\n          ],\r\n          \"TubeSerial\": [\r\n            \"SIHIRJT5786\"\r\n          ]\r\n        }\r\n      ]\r\n    }\r\n  ]\r\n}"
        data_json = json.loads(data)
        result = gbf._extract_tracking_info(data_json)

        self.assertIn("EDROP-00014", result)
        self.assertIn("2025-01-23", result['EDROP-00014']['date_kit_shipped'])
        self.assertIn("270000004830", result['EDROP-00014']['kit_tracking_n'])
        self.assertIn('XXXXXXXXXXXX', result['EDROP-00014']['return_tracking_n'])
        self.assertIn('SIHIRJT5786', result['EDROP-00014']['tube_serial_n'])

# To-Do:Test the confirmations flow to get the exact response of the post request
# and then mock it
    @patch("track.gbf.requests.post")
    def test_check_confirmations_response(self, mock_response):
        mock_response = MagicMock()
        mock_response.status_code() = 201
        mock_response.json.return_value = {}

        result = gbf._check_confirmations_response()