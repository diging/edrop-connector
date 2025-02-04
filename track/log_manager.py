import logging

from django_apscheduler.models import DjangoJobExecution

from track.models import *


logger = logging.getLogger(__name__)


class LogManager:

    def start_order_log(self, order_number):
        existing_log = OrderLog.objects.filter(order_number=order_number, is_complete=False).first()
        if existing_log:
            self.complete_log(existing_log)
        order_log = OrderLog.objects.create(order_number=order_number)
        return order_log

    def start_confirmation_log(self):
        existing_log = ConfirmationCheckLog.objects.filter(is_complete=False).first()
        if existing_log:
            self.complete_log(existing_log)
        job_id = DjangoJobExecution.objects.latest('run_time').id
        conf_log = ConfirmationCheckLog.objects.create(job_id=job_id)
        return conf_log
    
    def get_confirmation_log(self):
        return ConfirmationCheckLog.objects.filter(is_complete=False).first()
    
    def get_order_log(self, order_number):
        return OrderLog.objects.filter(order_number=order_number, is_complete=False).first()

    def append_to_apscheduler_log(self, log, level, message):
        log.append_to_apscheduler_log(level, message)
    
    def append_to_orders_log(self, log, level, message):
        log.append_to_orders_log(level, message)
        
    def append_to_gbf_log(self, log, level, message):
        log.append_to_gbf_log(level, message)
    
    def append_to_redcap_log(self, log, level, message):
        log.append_to_redcap_log(level, message)

    def complete_log(self, log):
        log.complete_log()