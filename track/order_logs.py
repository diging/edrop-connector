import logging
from track.models import OrderLog 

logger = logging.getLogger(__name__)

def create_order_log():
    order_log = OrderLog.objects.create()
    global order_log_id
    order_log_id = order_log.id

def get_log_id():
    return order_log_id

def _log_and_save(log_level, message, log_prop, order_log_id):
    order_log = OrderLog.objects.filter(id=order_log_id).first()
    # Dynamically append log text to either redcap, gbf, or apsscheduler object properties
    setattr(order_log, log_prop, getattr(order_log, log_prop, '') + f'{log_level.upper()}: {message}\n')
    order_log.save()

    if log_level == 'info':
        logger.info(message)
    elif log_level == 'error':
        logger.error(message)
    elif log_level == 'debug':
        logger.debug(message)