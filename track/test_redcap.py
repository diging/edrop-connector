import xml.etree.ElementTree as ET
from datetime import datetime
from http import HTTPStatus

import pytest
import requests
import pytz

# Import the functions from your module.
from redcap import get_record_info, set_order_number, set_tracking_info

# --------------------------------------------------------------------
# Helper Classes and Fixtures
# --------------------------------------------------------------------

class FakeResponse:
    """
    A fake response object to simulate requests.Response.
    """
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

class FakeSettings:
    """
    A fake settings object to simulate Django settings.
    """
    REDCAP_TOKEN = "TEST_TOKEN"
    REDCAP_URL = "http://test.redcap.url"
    REQUEST_TIMEZONE = "UTC"

@pytest.fixture(autouse=True)
def fake_settings(monkeypatch):
    """
    Automatically patch the settings in the module under test with FakeSettings.
    """
    monkeypatch.setattr("redcap.settings", FakeSettings)

@pytest.fixture(autouse=True)
def print_test_name(request):
    """
    Automatically print the name of each test as it starts.
    """
    print("\nRunning test: " + request.node.name)

# --------------------------------------------------------------------
# Tests for get_record_info
# --------------------------------------------------------------------

def test_get_record_info_success(monkeypatch):
    """
    Test that get_record_info successfully returns a record when REDCap responds with a record.
    """
    # Prepare a fake record that REDCap might return.
    fake_record = {
        'record_id': '1',
        'first_name': 'John',
        'last_name': 'Paper',
        'city': 'Tempe',
        'state': 'AZ',
        'zip': '85281',
        'street_1': '123 Main St',
        'street_2': 'Apt 404',
        'consent_complete': '2',
        'contact_complete': '2'
    }
    # fake response with HTTP 200 and a list containing our fake record.
    fake_response = FakeResponse(HTTPStatus.OK, [fake_record])

    def fake_post(url, data):
        # Return our fake response
        return fake_response

    # Patch requests.post to use our fake_post function.
    monkeypatch.setattr(requests, "post", fake_post)

    # Call the function and verify the returned record.
    record = get_record_info("1")
    assert record is not None
    assert record["record_id"] == "1"
    assert record["first_name"] == "John"
    assert record["last_name"] == "Paper"

def test_get_record_info_no_record(monkeypatch, caplog):
    """
    Test that get_record_info returns None if REDCap returns an empty list (no record found).
    """
    # Simulate a valid HTTP response with an empty list.
    fake_response = FakeResponse(HTTPStatus.OK, [])
    
    def fake_post(url, data):
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)
    record = get_record_info("nonexistent")
    # When no record is found, the function should return None.
    assert record is None
    # Optionally, check the log messages to verify proper logging.
    assert "REDCap HTTP Status" in caplog.text

def test_get_record_info_http_error(monkeypatch, caplog):
    """
    Test that get_record_info returns None and logs an error when a non-OK HTTP status is received.
    """
    # Simulate an HTTP error response.
    fake_response = FakeResponse(HTTPStatus.BAD_REQUEST, {"error": "Bad request"})
    
    def fake_post(url, data):
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)
    record = get_record_info("1")
    # Expecting None on error.
    assert record is None
    # Check that the error was logged.
    assert "REDCap HTTP Status" in caplog.text

# --------------------------------------------------------------------
# Tests for set_order_number
# --------------------------------------------------------------------

def test_set_order_number_success(monkeypatch):
    """
    Test that set_order_number creates the correct XML payload and that it is sent successfully.
    """
    captured_data = {}
    fake_response = FakeResponse(HTTPStatus.OK, {"count": 1})

    def fake_post(url, data):
        # Capture the 'data' parameter to inspect the XML payload.
        captured_data["data"] = data.get("data")
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)

    test_record_id = "123"
    test_order_number = "ORD-456"
    set_order_number(test_record_id, test_order_number)

    xml_data = captured_data.get("data")
    # Ensure that XML data was sent.
    assert xml_data is not None

    # Parse the XML and verify its structure and content.
    root = ET.fromstring(xml_data)
    items = root.findall("item")
    assert len(items) == 1

    item = items[0]
    # Verify each element in the XML.
    assert item.find("record_id").text == test_record_id
    assert item.find("kit_order_n").text == test_order_number
    assert item.find("kit_status").text == "ORD"
    # Verify that the date is in the expected format (YYYY-MM-DD).
    date_text = item.find("date_kit_request").text
    datetime.strptime(date_text, "%Y-%m-%d")

def test_set_order_number_http_error(monkeypatch, caplog):
    """
    Test that set_order_number logs an error when the HTTP response indicates a failure.
    """
    fake_response = FakeResponse(HTTPStatus.BAD_REQUEST, {"error": "Bad request"})
    
    def fake_post(url, data):
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)
    set_order_number("1", "ORD-789")
    # Verify that an error related to the HTTP status is logged.
    assert "HTTP Status" in caplog.text

# --------------------------------------------------------------------
# Tests for set_tracking_info
# --------------------------------------------------------------------

def test_set_tracking_info_success(monkeypatch):
    """
    Test that set_tracking_info correctly filters orders with a ship_date, constructs the XML,
    and sends the correct data.
    """
    # Define a dummy order class to simulate order objects.
    class DummyOrder:
        def __init__(self, record_id, ship_date, tracking_nrs, return_tracking_nrs, tube_serials):
            self.record_id = record_id
            self.ship_date = ship_date
            self.tracking_nrs = tracking_nrs
            self.return_tracking_nrs = return_tracking_nrs
            self.tube_serials = tube_serials

    # Create three orders:
    # order1 and order3 have a ship_date and should be included.
    # order2 does not have a ship_date and should be filtered out.
    order1 = DummyOrder("1", "2023-02-10", ["TN1", "TN2"], ["RTN1"], ["TS1"])
    order2 = DummyOrder("2", None, ["TN3"], [], ["TS2"])
    order3 = DummyOrder("3", "2023-02-11", [], ["RTN2", "RTN3"], [])

    captured_data = {}
    fake_response = FakeResponse(HTTPStatus.OK, {"count": 2})

    def fake_post(url, data):
        # Capture the XML data payload.
        captured_data["data"] = data.get("data")
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)

    # Call set_tracking_info with our dummy orders.
    set_tracking_info([order1, order2, order3])
    xml_data = captured_data.get("data")
    assert xml_data is not None

    # Parse the XML to verify its structure.
    root = ET.fromstring(xml_data)
    items = root.findall("item")
    # Only order1 and order3 should be present.
    assert len(items) == 2

    # Verify the details for order1.
    item1 = next(item for item in items if item.find("record_id").text == "1")
    assert item1.find("date_kit_shipped").text == "2023-02-10"
    assert item1.find("kit_tracking_n").text == "TN1, TN2"
    assert item1.find("kit_status").text == "TRN"
    assert item1.find("kit_tracking_return_n").text == "RTN1"
    assert item1.find("tubeserial").text == "TS1"

    # Verify the details for order3.
    item3 = next(item for item in items if item.find("record_id").text == "3")
    assert item3.find("date_kit_shipped").text == "2023-02-11"
    # Expect empty string when lists are empty.
    assert item3.find("kit_tracking_n").text == ""
    assert item3.find("kit_status").text == "TRN"
    assert item3.find("kit_tracking_return_n").text == "RTN2, RTN3"
    assert item3.find("tubeserial").text == ""

def test_set_tracking_info_no_orders(monkeypatch, caplog):
    """
    Test that set_tracking_info does not send any HTTP request if none of the orders have a ship_date.
    """
    call_count = 0

    def fake_post(url, data):
        nonlocal call_count
        call_count += 1
        return FakeResponse(HTTPStatus.OK, {"count": 0})

    monkeypatch.setattr(requests, "post", fake_post)

    # Create dummy orders that all have no ship_date.
    class DummyOrder:
        def __init__(self, record_id, ship_date):
            self.record_id = record_id
            self.ship_date = ship_date
            self.tracking_nrs = []
            self.return_tracking_nrs = []
            self.tube_serials = []

    orders = [DummyOrder("1", None), DummyOrder("2", None)]
    set_tracking_info(orders)
    # Verify that requests.post was not called.
    assert call_count == 0
    # Verify that a log message indicates no confirmations were received.
    assert "No confirmations received" in caplog.text

def test_set_tracking_info_http_error(monkeypatch, caplog):
    """
    Test that set_tracking_info logs an error when REDCap returns an HTTP error.
    """
    class DummyOrder:
        def __init__(self, record_id, ship_date, tracking_nrs, return_tracking_nrs, tube_serials):
            self.record_id = record_id
            self.ship_date = ship_date
            self.tracking_nrs = tracking_nrs
            self.return_tracking_nrs = return_tracking_nrs
            self.tube_serials = tube_serials

    # Create a dummy order with all required fields.
    order = DummyOrder("1", "2023-03-15", ["TN1"], ["RTN1"], ["TS1"])
    
    def fake_post(url, data):
        # Simulate an HTTP error.
        return FakeResponse(HTTPStatus.BAD_REQUEST, {"error": "Bad request"})

    monkeypatch.setattr(requests, "post", fake_post)
    set_tracking_info([order])
    # Check that the log contains an error regarding the HTTP status.
    assert "HTTP Status" in caplog.text

def test_set_tracking_info_order_with_empty_lists(monkeypatch):
    """
    Test that if tracking numbers or tube serial lists are empty, the XML fields are empty strings.
    """
    class DummyOrder:
        def __init__(self, record_id, ship_date):
            self.record_id = record_id
            self.ship_date = ship_date
            self.tracking_nrs = []         # Empty tracking numbers.
            self.return_tracking_nrs = []    # Empty return tracking numbers.
            self.tube_serials = []           # Empty tube serials.

    order = DummyOrder("4", "2023-04-01")
    captured_data = {}
    fake_response = FakeResponse(HTTPStatus.OK, {"count": 1})

    def fake_post(url, data):
        # Capture the XML payload.
        captured_data["data"] = data.get("data")
        return fake_response

    monkeypatch.setattr(requests, "post", fake_post)
    set_tracking_info([order])
    xml_data = captured_data.get("data")
    assert xml_data is not None

    # Parse the XML and verify that empty lists produce empty string values.
    root = ET.fromstring(xml_data)
    items = root.findall("item")
    assert len(items) == 1
    item = items[0]
    assert item.find("kit_tracking_n").text == ""
    assert item.find("kit_tracking_return_n").text == ""
    assert item.find("tubeserial").text == ""