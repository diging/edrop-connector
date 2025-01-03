from django.db import models

# Create your models here.
class Order(models.Model):
    # REDCap data
    project_id = models.CharField(max_length=255)
    initiated_by = models.CharField(max_length=255) # REDCap user who initiated the order
    redcap_url = models.CharField(max_length=255)
    project_url = models.CharField(max_length=255)
    record_id = models.CharField(max_length=255) # which record was created/modified

    # GBF data
    tracking_nr = models.CharField(max_length=255)

    INITIATED = 'IN'
    IN_PROGRESS = "PR"
    # TODO: are there more in between?
    DONE = "DO"

    CHOICES = {
        INITIATED: "Initiated",
        IN_PROGRESS: "In Progress",
        DONE: "Completed"
    }
    order_status = models.CharField(max_length=3, choices=CHOICES)