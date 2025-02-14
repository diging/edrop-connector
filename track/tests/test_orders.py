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

# Create a logger for this test module.
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
    
    @patch("track.orders.gbf.create_order")
    @patch("track.orders.redcap.set_order_number")
    @patch("track.orders.redcap.get_record_info")
    def test_place_order_failure_gbf(self, mock_get_record_info, mock_set_order_number, mock_create_order):
        """
        Test that if GBF fails to create the order (returns False), place_order creates the Order
        but then resets its status back to PENDING and does not call redcap.set_order_number.
        """
        logger.debug("Running test_place_order_failure_gbf: Simulating complete record but GBF order creation failure.")
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
        mock_create_order.return_value = False  # Simulate failure from GBF
        
        order = place_order(self.record_id, self.project_id, self.project_url)
        logger.debug("Order created with GBF failure: %s", order)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.order_status, Order.PENDING)
        mock_set_order_number.assert_not_called()
        logger.debug("redcap.set_order_number was not called due to GBF failure.")
    
    @patch("track.orders.redcap.set_order_number")
    def test_store_order_number_in_redcap(self, mock_set_order_number):
        """
        Test that store_order_number_in_redcap calls redcap.set_order_number with the correct record_id
        and order.order_number.
        """
        logger.debug("Running test_store_order_number_in_redcap.")
        order = Order.objects.create(
            record_id=self.record_id,
            project_id=self.project_id,
            project_url=self.project_url,
            order_status=Order.INITIATED,
            order_number="EDROP-00001"
        )
        store_order_number_in_redcap(self.record_id, order)
        mock_set_order_number.assert_called_once_with(self.record_id, order.order_number)
        logger.debug("redcap.set_order_number was called with record_id=%s and order_number=%s", self.record_id, order.order_number)
    
    @patch("track.orders.redcap.set_tracking_info")
    @patch("track.orders.gbf.get_order_confirmations")
    def test_check_orders_shipping_info(self, mock_get_order_confirmations, mock_set_tracking_info):
        """
        Test that check_orders_shipping_info:
          - Retrieves order numbers for orders with status INITIATED.
          - Calls gbf.get_order_confirmations with the list of order numbers.
          - Updates the order with the shipping info.
          - Calls redcap.set_tracking_info with the updated orders.
        """
        logger.debug("Running test_check_orders_shipping_info: Creating order with status INITIATED.")
        # Create an order with status INITIATED.
        order = Order.objects.create(
            record_id=self.record_id,
            project_id=self.project_id,
            project_url=self.project_url,
            order_status=Order.INITIATED,
            order_number="EDROP-00002"
        )
        # Simulate tracking info returned from GBF.
        tracking_info = {
            "EDROP-00002": {
                "date_kit_shipped": "2025-03-01",
                "kit_tracking_n": ["TRACK123"],
                "return_tracking_n": ["RET123"],
                "tube_serial_n": ["TUBE123"]
            }
        }
        mock_get_order_confirmations.return_value = tracking_info
        
        # Execute the function to check shipping info.
        check_orders_shipping_info()
        logger.debug("check_orders_shipping_info executed.")
        
        updated_order = Order.objects.get(order_number="EDROP-00002")
        self.assertEqual(updated_order.ship_date, "2025-03-01")
        self.assertEqual(updated_order.order_status, Order.SHIPPED)
        self.assertEqual(updated_order.tracking_nrs, ["TRACK123"])
        self.assertEqual(updated_order.return_tracking_nrs, ["RET123"])
        self.assertEqual(updated_order.tube_serials, ["TUBE123"])
        logger.debug("Order updated with shipping info: %s", updated_order)
        
        # Verify that redcap.set_tracking_info was called with the updated order.
        mock_set_tracking_info.assert_called_once()
        # Verify that gbf.get_order_confirmations was called with the correct order number list.
        mock_get_order_confirmations.assert_called_once_with(["EDROP-00002"])
        logger.debug("gbf.get_order_confirmations and redcap.set_tracking_info were called as expected.")
    
    def test_update_orders_with_shipping_info(self):
        """
        Test that _update_orders_with_shipping_info updates an order's shipping fields correctly
        and returns a list of order numbers that have been updated.
        """
        logger.debug("Running test_update_orders_with_shipping_info.")
        order = Order.objects.create(
            record_id=self.record_id,
            project_id=self.project_id,
            project_url=self.project_url,
            order_status=Order.INITIATED,
            order_number="EDROP-00003"
        )
        tracking_info = {
            "EDROP-00003": {
                "date_kit_shipped": "2025-04-01",
                "kit_tracking_n": ["TRACK999"],
                "return_tracking_n": ["RET999"],
                "tube_serial_n": ["TUBE999"]
            }
        }
        shipped_orders = _update_orders_with_shipping_info(tracking_info)
        logger.debug("Shipped orders returned: %s", shipped_orders)
        
        self.assertIn("EDROP-00003", shipped_orders)
        updated_order = Order.objects.get(order_number="EDROP-00003")
        self.assertEqual(updated_order.ship_date, "2025-04-01")
        self.assertEqual(updated_order.order_status, Order.SHIPPED)
        self.assertEqual(updated_order.tracking_nrs, ["TRACK999"])
        self.assertEqual(updated_order.return_tracking_nrs, ["RET999"])
        self.assertEqual(updated_order.tube_serials, ["TUBE999"])
        logger.debug("Order %s successfully updated with shipping info.", updated_order.order_number)