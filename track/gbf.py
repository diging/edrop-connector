from django.conf import settings
import requests, json
from http import HTTPStatus
import logging, inspect

from track.models import *
from track.log_manager import LogManager

logger = logging.getLogger(__name__)
log_manager = LogManager()


def create_order(order, adress_data):
    """
    Generates an order number and saves it in the order object. Then places an order with GBF.

    Returns:
     - true if placing the order was successful, false otherwise
    """
    order_number = _generate_order_number(order)
    order.order_number = order_number
    order.save()

    log_manager.start_order_log(order_number)
    # generate order json
    order_json = _generate_order_json(order, adress_data)

    # we cannot store PII (which the shipping address is, 
    # so this is here just for testing purposes and should not be executed in production)
    #logger.error(order_json)

    message = f"Placing order {order.order_number} with GBF."
    log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message, order_number)
    logger.info(message)
    
    # make order with GBF
    order_response = _place_order_with_GBF(order_json, order_number)

    return _check_order_response(order_response, order_number)

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

def _place_order_with_GBF(order_json, order_number):
    """
    Makes a POST request to the GBF endpoint /oap/api/order with the proper
    order Json. 

    Returns:
    - True if GBF returns true
    - False if GBF returns anything else than a status code 200
    """
    # make post request to GBF
    # By default requests should be made as "test" via an environment variable.
    # Once we go live, the environemnt variable needs to be set to true explictly.
    headers = {
        'Authorization': f'Bearer {settings.GBF_TOKEN}',
        'Content-Type': 'application/json'
        }

    response = requests.post(f"{settings.GBF_URL}oap/api/order", data=order_json, headers=headers)
    
    message = "Response from GBF:"
    log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message, order_number)
    logger.info(message)

    log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, response, order_number)
    logger.info(response)
    
    return response

def _check_order_response(response, order_number):
    response_body = response.json()
    log_manager.append_to_gbf_log(LogManager.LEVEL_DEBUG, response_body, order_number)
    logger.debug(response_body)
    if response.status_code != HTTPStatus.OK:
        message = f"Could not submit order {order_number} to GBF."
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message, order_number)
        logger.error(message)

        message = response
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message, order_number)
        logger.error(message)
        
        message = {response_body}
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message, order_number)
        logger.error(message)
        return False
    
    if "success" not in response_body or response_body["success"] != True:
        message = f"Could not submit order {order_number} to GBF."
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message, order_number)
        logger.error(message)
        
        message = response_body
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message, order_number)
        logger.error(message)
        return False
    
    message = f'Order {order_number} has been successfully placed with GBF!'
    log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message, order_number)
    logger.info(message)
    log_manager.complete_log(order_number)
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
    message = f"Getting GBF Order Confirmations for the following order numbers: {order_numbers}"
    log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message)
    logger.info(message)

    headers = {'Authorization': f'Bearer {settings.GBF_TOKEN}'}
    content = {'orderNumbers': order_numbers, 'format': 'json'}
    logger.debug('Sending to GBF:')
    logger.debug(content)
    log_manager.append_to_gbf_log(LogManager.LEVEL_DEBUG, content)
    try:
        response = requests.post(f"{settings.GBF_URL}oap/api/confirm2", data=content, headers=headers)
        response.raise_for_status()  # Raises an exception for bad status codes
        
        logger.debug(response.json())
    except requests.exceptions.HTTPError as err:
        message = f"Could not get order confirmation from GBF for the following order numbers: {order_numbers}."
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)
        
        message = err
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)
        return None

    response_body = response.json()
    # if for some reason GBF does not return a success response
    if response_body['success'] != True:
        message = "GBF returned success is false."
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)

        message = response_body
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)

    if "dataArray" not in response_body or not response_body["dataArray"]:
        message = "No GBF confirmations available."
        log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message)
        logger.info(message)
        return None
    
    # GBF sends one object in a list in 'dataArray', so we'll use the first one
    data_object = response_body["dataArray"][0]
    if 'format' not in data_object or data_object["format"] != "json":
        message = "GBF did not send json back."
        log_manager.append_to_gbf_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)
        return None
    
    if 'data' not in data_object or not data_object["data"]:
        message = "No GBF confirmations available."
        log_manager.append_to_gbf_log(LogManager.LEVEL_INFO, message)
        logger.info(message)
        return None
    
    confirmations = json.loads(data_object["data"])

    return _extract_tracking_info(confirmations)

def _extract_tracking_info(confirmations):
    tracking_info = {}
    if "ShippingConfirmations" in confirmations:
        for shipping_confirmation in confirmations['ShippingConfirmations']:
            tracking_info[shipping_confirmation['OrderNumber']] = {
                'date_kit_shipped': shipping_confirmation['ShipDate'] if 'ShipDate' in shipping_confirmation else None,
                'kit_tracking_n': shipping_confirmation['Tracking'] if 'Tracking' in shipping_confirmation else None,
                #filter for items with return tracking numbers and returns tracking numbers
                'return_tracking_n': [return_track if 'Items' in shipping_confirmation else None for item in shipping_confirmation['Items'] if 'ReturnTracking' in item for return_track in item['ReturnTracking']],
                #filter for items with return tracking numbers and returns tracking numbers
                'tube_serial_n': [tube_serial if 'Items' in shipping_confirmation else None for item in shipping_confirmation['Items'] if 'TubeSerial' in item for tube_serial in item['TubeSerial']]
            }  
    return tracking_info   


