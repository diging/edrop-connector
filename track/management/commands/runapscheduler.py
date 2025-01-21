import logging
from django.conf import settings

from track.models import *
from track import orders
from track import gbf
from track import redcap

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)


def check_for_tracking_info_job():
    logger.error("Running my job.")
    tracking_info = {}
    order_numbers = []

    orders_initiated = Order.objects.filter(order_status=Order.INITIATED)
  
    for order in orders_initiated:
        order_numbers.append(order.order_number)

    confirmed_orders = gbf.get_order_confirmations(order_numbers)
  
    for shipping_confirmation in confirmed_orders['ShippingConfirmations']:
        tracking_info[shipping_confirmation['OrderNumber']] = {
        'date_kit_shipped': shipping_confirmation['ShipDate'],
        'kit_tracking_n': shipping_confirmation['Tracking'],
        #filte for items with return tracking numbers and returns tracking numbers
        'return_tracking_n': [return_track for item in shipping_confirmation['Items'] if 'ReturnTracking' in item for return_track in item['ReturnTracking']]
        }

    #tracking info example
    #{'123': {'date_kit_shipped': '2023-01-12', 'kit_tracking_n': ['outbound tracking 1', 'outbound tracking 2'], 'return_tracking_n': ['inbound tracking', 'inbound tracking2']}}
    orders.update_orders(tracking_info)

    #retrieve the updated order objects
    order_objects = Order.objects.filter(order_number__in=order_numbers)

    redcap.set_tracking_info(order_objects)

    logger.error("Job completed.")

# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way. 
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
  

class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
        check_for_tracking_info_job,
        trigger=CronTrigger(day=settings.CRON_JOB_FREQUENCEY), # set parameter to e.g. second="*/10" to run every 10 seconds
        id="check_for_tracking_numbers_job",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
        )
        logger.info("Added job 'check_for_tracking_numbers_job'.")

        scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(
            day_of_week="mon", hour="00", minute="00"
        ),  # Midnight on Monday, before start of the next work week.
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
        )
        logger.info(
        "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")