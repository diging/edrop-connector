from track.models import *
from track import redcap   
from track import gbf
import logging

logger = logging.getLogger(__name__)

def create_order(record_id, project_id, project_url):
    new_order = Order.objects.create(record_id=record_id, project_id=project_id, project_url=project_url,order_status=Order.PENDING)
    new_order.save()

    address_data = redcap.get_record_info(record_id)

    logger.error("Sending to:")
    logger.error(address_data)

    new_order.order_status = Order.INITIATED

    order_number = gbf.create_order(new_order, address_data)
    new_order.order_number = order_number
    new_order.save()

    return new_order


