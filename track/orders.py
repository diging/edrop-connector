from track.models import *
from track import redcap   
from track import gbf
import logging
import json

logger = logging.getLogger(__name__)

def create_order(record_id, project_id, project_url):
    address_data = redcap.get_record_info(record_id)
    
    # we need to make sure that the original request actually came from REDCap, so we make sure
    # that the record in REDCap is indeed set to consent_complete = 2 (complete)
    if address_data['consent_complete'] != '2':
        return None

    new_order = Order.objects.create(record_id=record_id, project_id=project_id, project_url=project_url,order_status=Order.PENDING)
    new_order.save()

    new_order.order_status = Order.INITIATED

    gbf.create_order(new_order, address_data)
    
    return new_order


def store_order_number_in_redcap(record_id, order):
    redcap.set_order_number(record_id, order.order_number)