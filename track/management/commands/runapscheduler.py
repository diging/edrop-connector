import logging
import requests
from django.conf import settings

from track.models import *
from track import orders

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

  headers = {'Authorization': f'Bearer {settings.GBF_TOKEN}'}
  content = {'orderNumbers': order_numbers, 'format': 'json'}
  response = requests.post(f"{settings.GBF_URL}oap/api/confirm2", data=content, headers=headers)
  
  logger.error(response)
  logger.error(response.json())

  for shipping_confirmation in response['ShippingConfirmations']:
    tracking_info[shipping_confirmation['OrderNumber']] = {
      'date_kit_shipped': shipping_confirmation['ShipDate'],
      'kit_tracking_n': shipping_confirmation['Tracking'],
      'return_tracking_n': shipping_confirmation['Items']['ReturnTracking']
    }
  
  orders.update_orders



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
      trigger=CronTrigger(second='*/15'), # set parameter to e.g. second="*/10" to run every 10 seconds
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