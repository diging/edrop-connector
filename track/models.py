import logging, inspect
from datetime import datetime
import pytz

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField

logger = logging.getLogger(__name__)

# Create your models here.
class Order(models.Model):
    # REDCap data
    project_id = models.CharField(max_length=255)
    initiated_by = models.CharField(max_length=255, blank=True, null=True) # REDCap user who initiated the order
    redcap_url = models.CharField(max_length=255, blank=True, null=True)
    project_url = models.CharField(max_length=255, blank=True, null=True)
    record_id = models.CharField(max_length=255) # which record was created/modified
    order_number = models.CharField(max_length=255, blank=True, null=True)

    # GBF data
    ship_date = models.CharField(max_length=255, blank=True, null=True)
    return_tracking_nrs = ArrayField(models.CharField(), blank=True, null=True)
    tracking_nrs = ArrayField(models.CharField(), blank=True, null=True)

    PENDING = 'PE'
    INITIATED = 'IN'
    SHIPPED = "SH"
    # TODO: are there more in between?
    DONE = "DO"

    CHOICES = {
        PENDING: "Pending",
        INITIATED: "Initiated",
        SHIPPED: "Kit has shipped",
        DONE: "Completed"
    }
    order_status = models.CharField(max_length=3, choices=CHOICES, blank=True, null=True)


class Log(models.Model):
    apscheduler = models.TextField(default='', blank=True, null=True)
    orders = models.TextField(default='', blank=True, null=True)
    gbf = models.TextField(default='', blank=True, null=True)
    redcap = models.TextField(default='', blank=True, null=True)
    is_complete = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(default=datetime.now(pytz.timezone(settings.REQUEST_TIMEZONE)))

    def append_to_apscheduler_log(self, level, message):
        if not self.is_complete:
            self.apscheduler += f'{level.upper()}: {message}\n'
            self.save(update_fields=['apscheduler'])
        else:
            logger.error(f'{inspect.stack()[0][3]}: Log has already been completed. Unable to append to log.')

    def append_to_orders_log(self, level, message):
        if not self.is_complete:
            self.orders += f'{level.upper()}: {message}\n'
            self.save(update_fields=['orders'])
        else:
            logger.error(f'{inspect.stack()[0][3]}: Log has already been completed. Unable to append to log.')

    def append_to_gbf_log(self, level, message):
        if not self.is_complete:
            self.gbf += f'{level.upper()}: {message}\n'
            self.save(update_fields=['gbf'])
        else:
            logger.error(f'{inspect.stack()[0][3]}: Log has already been completed. Unable to append to log.')

    def append_to_redcap_log(self, level, message):
        if not self.is_complete:
            self.redcap += f'{level.upper()}: {message}\n'
            self.save(update_fields=['redcap'])
        else:
            logger.error(f'{inspect.stack()[0][3]}: Log has already been completed. Unable to append to log.')

    def complete_log(self):
        if not self.is_complete:
            self.is_complete = True
            self.end_time = datetime.now(pytz.timezone(settings.REQUEST_TIMEZONE))
            self.save(update_fields=['is_complete', 'end_time'])
            logger.info(f'{inspect.stack()[0][3]}: Log {self.id}: Complete!')
    
    class Meta:
        abstract = True

class OrderLog(Log):
    order_number = models.CharField(max_length=255, blank=True, null=True)

class ConfirmationCheckLog(Log):
    job_id = models.CharField(max_length=255, blank=True, null=True)