import logging, inspect
from django.conf import settings

from track.models import *
from track import orders
from track.log_manager import LogManager

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)
log_manager = LogManager()

def check_for_tracking_info_job():
    log = log_manager.start_confirmation_log()
    message = f"Started Cron Job {log.job_id}."
    log_manager.append_to_apscheduler_log(log, 'info', message)
    logger.info(message)

    message = 'Checking for tracking info.'
    log_manager.append_to_apscheduler_log(log, 'info', message)
    logger.info(message)

    orders.check_orders_shipping_info()

    message = "Tracking info check completed."
    log_manager.append_to_apscheduler_log(log, 'info', message)
    logger.info(message)

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
            trigger=CronTrigger(second="*/10"), # set parameter to e.g. second="*/10" to run every 10 seconds
            id="check_for_tracking_numbers_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        message = f"Added job 'check_for_tracking_numbers_job'."
        logger.info(message)

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        message = "Added weekly job: 'delete_old_job_executions'."
        logger.info(message)

        try:
            message = "Starting scheduler..."
            logger.info(message)
            scheduler.start()
        except KeyboardInterrupt:
            log = log_manager.get_confirmation_log()
            message = "Stopping scheduler..."
            log_manager.append_to_apscheduler_log(log, 'info', message)
            logger.info(message)

            scheduler.shutdown()
            message = "Scheduler shut down successfully!"
            log_manager.append_to_apscheduler_log(log, 'info', message)
            logger.info(message)
            
            log_manager.complete_log(log)