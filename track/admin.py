from django.contrib import admin
from track.models import *
from django.http import HttpResponseRedirect
from django.urls import path
import logging
from track import orders

logger = logging.getLogger(__name__)


# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "track/check_orders.html"

    list_display = ["record_id", "order_number", "tracking_nrs", "return_tracking_nrs", "tube_serials", "order_status", "ship_date"]

class ConfirmationCheckLogAdmin(admin.ModelAdmin):
    list_display = ["id", "job_id", "start_time", "end_time", "is_complete"]
    fields = ("job_id", "apscheduler", "orders", "gbf", "redcap", "end_time", "is_complete")
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('check_order_status/', self.call_check_order_status),
        ]
        return my_urls + urls
    
    def call_check_order_status(self, request):
        logger.info("Initiatied check for tracking info") 
        orders.check_orders_shipping_info()
        logger.info("Tracking info check completed.")
        return HttpResponseRedirect("../")

class OrderLogAdmin(admin.ModelAdmin):
    list_display = ["id", "order_number", "start_time", "end_time", "is_complete"]
    fields = ("order_number", "redcap", "orders", "gbf", "end_time", "is_complete")

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLog, OrderLogAdmin)
admin.site.register(ConfirmationCheckLog, ConfirmationCheckLogAdmin)
