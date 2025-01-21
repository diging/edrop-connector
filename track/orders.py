from track.models import *
from track import redcap   
from track import gbf
import logging
import json

logger = logging.getLogger(__name__)

def place_order(record_id, project_id, project_url):
    address_data = redcap.get_record_info(record_id)
    
    # we need to make sure that the original request actually came from REDCap, so we make sure
    # that the record in REDCap is indeed set to consent_complete = 2 (complete)
    if address_data['consent_complete'] != '2':
        return None

    order = Order.objects.filter(record_id=record_id).first()
    if not order:
        order = Order.objects.create(record_id=record_id, project_id=project_id, project_url=project_url,order_status=Order.PENDING)
        
    # to be safe, we'll first set it to initiated in case two process for whatever reason do the samething
    # we don't want to order two kits
    order.order_status = Order.INITIATED
    order.save()

    gbf.create_order(order, address_data)
    
    return order


def store_order_number_in_redcap(record_id, order):
    redcap.set_order_number(record_id, order.order_number)