from track.models import *
from track import redcap   
from track import gbf
from django.conf import settings
import logging, inspect

logger = logging.getLogger(__name__)

def place_order(record_id, project_id, project_url):
    address_data = redcap.get_record_info(record_id)
    
    # we need to make sure that the original request actually came from REDCap, so we make sure
    # that the record in REDCap is indeed set to contact_complete = 2 (complete)
    if address_data[settings.REDCAP_FIELD_TO_BE_COMPLETE] != '2':
        return None

    order = Order.objects.filter(record_id=record_id).first()
    if not order:
        order = Order.objects.create(record_id=record_id, project_id=project_id, project_url=project_url,order_status=Order.PENDING)
        
    # to be safe, we'll first set it to initiated in case two process for whatever reason do the samething
    # we don't want to order two kits
    order.order_status = Order.INITIATED
    order.save()

    success = gbf.create_order(order, address_data)
    
    if success:
        # post order number back to redcap
        store_order_number_in_redcap(record_id, order)
    else:
        # set order status back to pending, so we can try again.
        order.order_status = Order.PENDING
        order.save()

    return order


def store_order_number_in_redcap(record_id, order):
    redcap.set_order_number(record_id, order.order_number)

def check_orders_shipping_info():
    """
    Method to check the shipping status of all orders not yet shipped. This method will retrieve all orders
    from the database with status "INITIATED", which are kits that are ordered but not shipped yet. It will
    request order confirmations for all these order from GBF. If shipping information is provided (ship date and tracking
    numbers), then this information will be stored in the database and send to REDCap.
    """
    # find ids of all orders that have not been shipped yet
    orders_initiated = Order.objects.filter(order_status=Order.INITIATED).values_list("order_number", flat=True)
    
    order_numbers = list(orders_initiated)
    # get order confirmation from gbf
    tracking_info = gbf.get_order_confirmations(order_numbers)
    
    shipped_orders = _update_orders_with_shipping_info(tracking_info)

    #retrieve the updated order objects
    order_objects = Order.objects.filter(order_number__in=shipped_orders)
    redcap.set_tracking_info(order_objects)

def _update_orders_with_shipping_info(tracking_info):
    """
    This method takes a dictionary with order confirmation information and updates the order
    objects in the database accordingly.

    Expected tracking info dictionary:
    {
        'EDROP-001': {
            'date_kit_shipped': '2023-01-12', 
            'kit_tracking_n': ['outbound tracking 1', 'outbound tracking 2'], 
            'return_tracking_n': ['inbound tracking', 'inbound tracking2']
        }
    }

    Returns:
        - a list of all order numbers that have shipping date and tracking information
    """
    shipped_orders = []
    for order_number in tracking_info:
        try:
            order = Order.objects.get(order_number=order_number)
        except Exception as e:
            logger.error(e)
            logger.error(f"{__name__}.{inspect.stack()[0][3]}: Order {order_number} not found.")
            continue
        
        # if order has not shipped yet, we don't need to continue
        if not tracking_info[order.order_number]['date_kit_shipped']: 
            continue

        order.ship_date = tracking_info[order.order_number]['date_kit_shipped']
        order.order_status = Order.SHIPPED
        shipped_orders.append(order.order_number)

        if tracking_info[order.order_number]['kit_tracking_n']:
            order.tracking_nrs = tracking_info[order.order_number]['kit_tracking_n']
        if tracking_info[order.order_number]['return_tracking_n']:
            order.return_tracking_nrs = tracking_info[order.order_number]['return_tracking_n']
        order.save()
    
    return shipped_orders
        