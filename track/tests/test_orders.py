# test_orders.py

import logging
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from track.models import Order
from track.orders import (
    place_order,
    store_order_number_in_redcap,
    check_orders_shipping_info,
    _update_orders_with_shipping_info
)

logger = logging.getLogger(__name__)

# Override the setting used in orders to check for record completeness.
@override_settings(REDCAP_FIELD_TO_BE_COMPLETE="contact_complete")
class TestOrders(TestCase):
    def setUp(self):
        # Setup common test parameters.
        self.record_id = "123"
        self.project_id = "proj_1"
        self.project_url = "http://example.com/project"
        logger.debug("TestOrders: setUp complete with record_id=%s, project_id=%s", self.record_id, self.project_id)
    
    @patch("track.orders.redcap.get_record_info")
    def test_place_order_incomplete_record(self, mock_get_record_info):
        """
        Test that if the REDCap record does not have the complete flag (i.e. contact_complete != '2'),
        place_order returns None.
        """
        # Simulate a record with incomplete data.
        logger.debug("Running test_place_order_incomplete_record: Simulating incomplete REDCap record.")
        mock_get_record_info.return_value = {"contact_complete": "1"}
        
        # Attempt to place the order.
        order = place_order(self.record_id, self.project_id, self.project_url)
        logger.debug("Order placement result for incomplete record: %s", order)
        
        # Expect no order to be created.
        self.assertIsNone(order)
    
    @patch("track.orders.gbf.create_order")
    @patch("track.orders.redcap.set_order_number")
    @patch("track.orders.redcap.get_record_info")
    def test_place_order_success(self, mock_get_record_info, mock_set_order_number, mock_create_order):
        """
        Test that when the record is complete (contact_complete == '2') and GBF order creation
        succeeds, place_order creates an Order with status INITIATED and calls redcap.set_order_number.
        """
        logger.debug("Running test_place_order_success: Simulating complete REDCap record and successful GBF order creation.")
        # Provide complete address data.
        address_data = {
            "contact_complete": "2",
            "first_name": "John",
            "last_name": "Doe",
            "street_1": "742 Evergreen Terrace",
            "street_2": "",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704",
        }
        mock_get_record_info.return_value = address_data

        # Define a fake create_order that simulates generating an order number.
        def fake_create_order(order, address_data):
            logger.debug("fake_create_order: Generating order number for order with record_id=%s", order.record_id)
            order.order_number = "EDROP-00003"
            order.save()
            return True

        # Set side effect to simulate a successful order creation.
        mock_create_order.side_effect = fake_create_order

        # Place the order.
        order = place_order(self.record_id, self.project_id, self.project_url)
        logger.debug("Order created: %s", order)
        
        # Verify that an order was created and its status is INITIATED.
        self.assertIsNotNone(order)
        self.assertEqual(order.order_status, Order.INITIATED)
        mock_create_order.assert_called_once()
        logger.debug("GBF.create_order was called successfully.")

        # Verify that redcap.set_order_number is called with the correct parameters.
        mock_set_order_number.assert_called_once_with(self.record_id, "EDROP-00003")
        logger.debug("redcap.set_order_number was called with record_id=%s and order_number=%s", self.record_id, "EDROP-00003")
    
