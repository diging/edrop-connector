import logging

from django_apscheduler.models import DjangoJobExecution

from track.models import *

logger = logging.getLogger(__name__)


class LogManager:

    LEVEL_INFO = "info"
    LEVEL_DEBUG = "debug"
    LEVEL_ERROR = "error"

    def start_order_log(self, order_number):
        existing_log = OrderLog.objects.filter(order_number=order_number, is_complete=False).first()
        if existing_log:
            self.complete_log(order_number)
        OrderLog.objects.create(order_number=order_number)

    def start_confirmation_log(self):
        existing_log = ConfirmationCheckLog.objects.filter(is_complete=False).first()
        if existing_log:
            self.complete_log()
        job_id = DjangoJobExecution.objects.filter(job='check_for_tracking_numbers_job').latest('run_time').id
        ConfirmationCheckLog.objects.create(job_id=job_id)

    def _get_log(self, order_number=None):
        if order_number:
            try:
                return OrderLog.objects.get(order_number=order_number, is_complete=False)
            except Exception as e:
                logger.error(e)
                logger.error("OrderLog not found.")
        else:
            log = ConfirmationCheckLog.objects.filter(is_complete=False).first()
            if log:
                return log
            else:
                logger.error("ConfirmationCheckLog not found.")
                
        return None

    def get_job_id(self):
        log = self._get_log()
        return log.job_id if log else None

    def get_log_id(self, order_number=None):
        log = self._get_log(order_number)
        return log.id if log else None

    def append_to_apscheduler_log(self, level, message):
        log = self._get_log()
        if log:
            log.append_to_apscheduler_log(level, message)
    
    def append_to_orders_log(self, level, message, order_number=None):
        log = self._get_log(order_number)
        if log:
            log.append_to_orders_log(level, message)
        
    def append_to_gbf_log(self, level, message, order_number=None):
        log = self._get_log(order_number)
        if log:
            log.append_to_gbf_log(level, message)
    
    def append_to_redcap_log(self, level, message, order_number=None):
        log = self._get_log(order_number)
        if log:
            log.append_to_redcap_log(level, message)

    def complete_log(self, order_number=None):
        log = self._get_log(order_number)
        if log:
            level = 'info'
            message = f'Log {log.id}: Complete!'
            if order_number:
                log.append_to_gbf_log(level, message)
            else:
                log.append_to_redcap_log(level, message)
            log.complete_log()

    def raise_error_flag(self, order_number=None):
        log = self._get_log(order_number)
        if log:
            log.raise_error_flag()
