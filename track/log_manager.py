import logging

from django_apscheduler.models import DjangoJobExecution

from track.models import *

logger = logging.getLogger(__name__)


class LogManager:

    def start_order_log(self, order_number):
        existing_log = OrderLog.objects.filter(order_number=order_number, is_complete=False).first()
        if existing_log:
            self.complete_log(order_number)
        OrderLog.objects.create(order_number=order_number)

    def start_confirmation_log(self):
        existing_log = ConfirmationCheckLog.objects.filter(is_complete=False).first()
        if existing_log:
            self.complete_log()
        job_id = DjangoJobExecution.objects.latest('run_time').id
        ConfirmationCheckLog.objects.create(job_id=job_id)

    def get_log(self, order_number=None):
        log = None
        if order_number:
            try:
                return OrderLog.objects.get(order_number=order_number, is_complete=False)
            except Exception as e:
                logger.error(f"{inspect.stack()[0][3]}: {e}")
                logger.error(f"{inspect.stack()[0][3]}: OrderLog not found.")
        else:
            log = ConfirmationCheckLog.objects.filter(is_complete=False).first()
            if log:
                return log
            else:
                logger.error(f"{inspect.stack()[0][3]}: ConfirmationCheckLog not found.")
                raise ConfirmationCheckLog.DoesNotExist("ConfirmationCheckLog not found.")

    def get_job_id(self):
        return self.get_log().job_id

    def get_log_id(self, order_number=None):
        log = self.get_log(order_number)
        return log.id

    def append_to_apscheduler_log(self, level, message):
        log = self.get_log()
        log.append_to_apscheduler_log(level, message)
    
    def append_to_orders_log(self, level, message, order_number=None):
        log = self.get_log(order_number)
        log.append_to_orders_log(level, message)
        
    def append_to_gbf_log(self, level, message, order_number=None):
        log = self.get_log(order_number)
        log.append_to_gbf_log(level, message)
    
    def append_to_redcap_log(self, level, message, order_number=None):
        log = self.get_log(order_number)
        log.append_to_redcap_log(level, message)

    def complete_log(self, order_number=None):
        log = self.get_log(order_number)

        level = 'info'
        message = f'Log {log.id}: Complete!'
        if order_number:
            log.append_to_gbf_log(level, message)
        else:
            log.append_to_apscheduler_log(level, message)
        log.complete_log()
