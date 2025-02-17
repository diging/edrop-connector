from django.conf import settings
import requests, json
from http import HTTPStatus
import logging

logger = logging.getLogger(__name__)

def create_order(order, adress_data):
    """
    Generates an order number and saves it in the order object. Then places an order with GBF.

    Returns:
     - true if placing the order was successful, false otherwise
    """
    order_number = _generate_order_number(order)
    order.order_number = order_number
    order.save()

    # generate order json
    order_json = _generate_order_json(order, adress_data)
    logger.error("Sending to GBF:")
    logger.error(order_json)
    
    # make order with GBF
    order_response = _place_order_with_GBF(order_json)

    return _check_order_response(order_response)

def _generate_order_number(order):
    """
    Generates an order number based on the primary key of the order object.
    """
    return "EDROP-%05d"%(order.pk)

def _generate_order_json(order, address_data):
    order_json = {
        "test": settings.GBF_TEST_FLAG,
        "orders": [
            {
                "orderNumber": order.order_number,
                "shippingInfo": {
                    "address": {
                        "company": f"{address_data['first_name'] if 'first_name' in address_data else ''} {address_data['last_name'] if 'last_name' in address_data else ''}",
                        "addressLine1": address_data['street_1'] if 'street_1' in address_data else '',
                        "addressLine2": address_data['street_2'] if 'street_2' in address_data else '', # in case we add this to redcap, we need to add
                        "city": address_data['city'] if 'city' in address_data else '',
                        "state": address_data['state'] if 'state' in address_data else '',
                        "zipCode": address_data['zip'] if 'zip' in address_data else '',
                        "country": settings.GBF_SHIPPING_COUNTRY,
                        "phone": address_data['phone'] if 'phone' in address_data else '',
                        "residential": True # see GitHub discussion #19 (shipping address)
                    },
                    "shipMethod": settings.GBF_SHIPPING_METHOD,
                },
                "lineItems": [
                    {
                    "itemNumber": settings.GBF_ITEM_NR,
                    "itemQuantity": settings.GBF_ITEM_QUANTITY,
                    }
                ]
            }
        ]
    }

    return json.dumps(order_json)


def _place_order_with_GBF(order_json):
    """
    Makes a POST request to the GBF endpoint /oap/api/order with the proper
    order Json. 

    Returns:
    - True if GBF returns true
    - False if GBF returns anything else than a status code 200
    """
    # make post request to GBF
    # By default requests should be made as "test" via an environment variable.
    # Once we go live, the environemnt variable needs to be set to true explictly,
    headers = {
        'Authorization': f'Bearer {settings.GBF_TOKEN}',
        'Content-Type': 'application/json'
        }
    response = requests.post(f"{settings.GBF_URL}oap/api/order", data=order_json, headers=headers)
    logger.error("Response from GBF:")
    logger.error(response)
    
    return response

def _check_order_response(response):
    response_body = response.json()
    if response.status_code != HTTPStatus.OK:
        logger.error("Could not submit order to GBF.")
        logger.error(response)
        logger.error(response_body)
        return False
    
    if "success" not in response_body or response_body["success"] != True:
        logger.error("Could not submit order to GBF.")
        logger.error(response_body)
        return False
    
    return True

def get_order_confirmations(order_numbers):
    """
    This method gets shipping confirmations from GBF for the given order numbers and returns:
    - date kit was shipped
    - tracking numbers
    - return tracking numbers

    GBF sends json like this:
    {
        "success": True,
        "dataArray": [
            {
                "format": "json",
                "data": "{\r\n  \"ShippingConfirmations\": [\r\n    {\r\n      \"OrderNumber\": \"EDROP-00014\",\r\n      \"Shipper\": \"\",\r\n      \"ShipVia\": \"FedEx Ground\",\r\n      \"ShipDate\": \"2025-01-23\",\r\n      \"ClientID\": \"\",\r\n      \"Tracking\": [\r\n        \"270000004830\"\r\n      ],\r\n      \"Items\": [\r\n        {\r\n          \"ItemNumber\": \"K-BAN-001\",\r\n          \"SerialNumber\": \"EV-05FCSG\",\r\n          \"ShippedQty\": 1,\r\n          \"ReturnTracking\": [\r\n            \"XXXXXXXXXXXX\"\r\n          ],\r\n          \"TubeSerial\": [\r\n            \"SIHIRJT5786\"\r\n          ]\r\n        }\r\n      ]\r\n    }\r\n  ]\r\n}"
            }
        ]
    }

    Returns:
    -  a dictionary of the form:
    {
        'EDROP-001': {
            'date_kit_shipped': '2023-01-12', 
            'kit_tracking_n': ['outbound tracking 1', 'outbound tracking 2'], 
            'return_tracking_n': ['inbound tracking', 'inbound tracking2'],
            'tube_serial_n': [tube serial1', 'tube serial2']
        }
    }
    """
    headers = {'Authorization': f'Bearer {settings.GBF_TOKEN}'}
    content = {'orderNumbers': order_numbers, 'format': 'json'}
    try:
        response = requests.post(f"{settings.GBF_URL}oap/api/confirm2", data=content, headers=headers)
        response.raise_for_status()  # Raises an exception for bad status codes
        logger.debug(response.json())
    except requests.exceptions.HTTPError as err:
        logger.error(f"Could not get order confirmation from GBF.")
        logger.error(err) 
        return None  
    
    response_body = response.json()
    if response_body['success'] != True:
        logger.error("GBF returned success is false.")
        logger.error(response_body)

    if "dataArray" not in response_body or not response_body["dataArray"]:
        logger.info("No GBF confirmations available.")
        return None
    
    # GBF sends one object in a list in 'dataArray', so we'll use the first one
    data_object = response_body["dataArray"][0]
    if 'format' not in data_object or data_object["format"] != "json":
        logger.error("GBF did not send json back.")
        return None
    
    if 'data' not in data_object or not data_object["data"]:
        logger.info("No GBF confirmations available.")
        return None
    
    confirmations = json.loads(data_object["data"])

    return _extract_tracking_info(confirmations)

def _extract_tracking_info(confirmations):
    tracking_info = {}
    if "ShippingConfirmations" in confirmations:
        for shipping_confirmation in confirmations['ShippingConfirmations']:
            tracking_info[shipping_confirmation['OrderNumber']] = {
                'date_kit_shipped': shipping_confirmation['ShipDate'],
                'kit_tracking_n': shipping_confirmation['Tracking'],
                #filter for items with return tracking numbers and returns tracking numbers
                'return_tracking_n': [return_track for item in shipping_confirmation['Items'] if 'ReturnTracking' in item for return_track in item['ReturnTracking']],
                #filter for items with return tracking numbers and returns tracking numbers
                'tube_serial_n': [tube_serial for item in shipping_confirmation['Items'] if 'TubeSerial' in item for tube_serial in item['TubeSerial']]
            }
    return tracking_info   


