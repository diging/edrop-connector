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
    """
    order_number = _generate_order_number(order)
    order.order_number = order_number
    order.save()

    log = log_manager.start_order_log(order.order_number)

    # generate order json
    order_json = _generate_order_json(order, adress_data)
    
    # make order with GBF
    _place_order_with_GBF(order_json)
    
    message = f'Order {order.order_nummber} has been successfully placed with GBF!'
    log_manager.append_to_gbf_log(log, 'info', message)
    logger.info(message)
    log_manager.complete_log(log)

    return order_number

def get_order_confirmations(order_numbers):
    """
    This method gets shipping confirmations from GBF for the given order numbers and returns:
    - date kit was shipped
    - tracking numbers
    - return tracking numbers

    Returns:
    -  a dictionary of the form:
    {
        'EDROP-001': {
            'date_kit_shipped': '2023-01-12', 
            'kit_tracking_n': ['outbound tracking 1', 'outbound tracking 2'], 
            'return_tracking_n': ['inbound tracking', 'inbound tracking2']
        }
    }
    """
    log = log_manager.get_confirmation_log()
    message = f"Getting GBF Order Confirmations for the following order numbers: {order_numbers}"
    log_manager.append_to_gbf_log(log, 'info', message)
    logger.info(message)

    headers = {'Authorization': f'Bearer {settings.GBF_TOKEN}'}
    content = {'orderNumbers': order_numbers, 'format': 'json'}
    try:
        response = requests.post(f"{settings.GBF_URL}oap/api/confirm2", data=content, headers=headers)
        response.raise_for_status()  # Raises an exception for bad status codes
    except requests.exceptions.HTTPError as err:
        message = f"{inspect.stack()[0][3]}: Could not get order confirmation from GBF for the following order numbers: {order_numbers}."
        log_manager.append_to_gbf_log(log, 'error', message)
        logger.error(message)
        message = f"{inspect.stack()[0][3]}: {err}"
        log_manager.append_to_gbf_log(log, 'error', message)
        logger.error(message)
        return None  

    confirmations = response.json()
    tracking_info = {}
    for shipping_confirmation in confirmations['ShippingConfirmations']:
        tracking_info[shipping_confirmation['OrderNumber']] = {
            'date_kit_shipped': shipping_confirmation['ShipDate'],
            'kit_tracking_n': shipping_confirmation['Tracking'],
            #filter for items with return tracking numbers and returns tracking numbers
            'return_tracking_n': [return_track for item in shipping_confirmation['Items'] if 'ReturnTracking' in item for return_track in item['ReturnTracking']]
        }  
    return tracking_info   

def _generate_order_number(order):
    """
    Generates an order number based on the primary key of the order object.
    """
    return "EDROP-%05d"%(order.pk)

def _generate_order_json(order, address_data):
    order_json = {
        "test": settings.GBF_TEST_FLAG,
        "orderNumber": order.order_number,
        "shippingInfo": {
            "address": {
                "company": f"{address_data['first_name'] if 'first_name' in address_data else ''} {address_data['last_name'] if 'last_name' in address_data else ''}",
                "addressLine1": address_data['street_1'] if 'street_1' in address_data else '',
                "addressLine2": "", # in case we add this to redcap, we need to add
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
    order_data = json.loads(order_json)
    log = log_manager.get_order_log(order_data['orderNumber'])

    headers = {'Authorization': f'Bearer {settings.GBF_TOKEN}'}
    response = requests.post(f"{settings.GBF_URL}oap/api/order", data=order_json, headers=headers)
    
    if response.status_code != HTTPStatus.OK:
        message = f"{inspect.stack()[0][3]}: Could not submit order to GBF."
        log_manager.append_to_gbf_log(log, 'error', message)
        logger.error(message)

        message = f'{inspect.stack()[0][3]}: {response}'
        log_manager.append_to_gbf_log(log, 'error', message)
        logger.error(message)
        return False
    return True
