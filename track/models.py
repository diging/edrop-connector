from django.db import models
#from django.contrib.postgres.fields import ArrayField

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
    #currently stores an array of orders as a string
    tracking_nr = models.CharField(max_length=255, blank=True, null=True)
    ship_date = models.CharField(max_length=255, blank=True, null=True)
    return_tracking_nr = models.CharField(max_length=255, blank=True, null=True)
    
    # multiple tracking numbers? see example ShippingConfirmation response
    # tracking_nrs = ArrayField(models.CharField())

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