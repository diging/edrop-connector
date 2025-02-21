from django.contrib import admin
from track.models import *
from django.http import HttpResponseRedirect
from django.urls import path
import logging
from track import orders
from django.contrib import messages
from track import gbf

logger = logging.getLogger(__name__)


# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "track/check_orders.html"

    list_display = ["record_id", "order_number", "tracking_nrs", "return_tracking_nrs", "tube_serials", "order_status", "ship_date"]
    actions = ['check_orders_status']

    def get_actions(self, request):
        actions = super().get_actions(request)
        return actions

    def check_orders_status(self, request, queryset):
        if not queryset:
            self.message_user(request, "No orders selected to check status.", messages.WARNING)
            return
            
        try:
            order_numbers = list(queryset.values_list('order_number', flat=True))
            queryset.update(order_status=Order.INITIATED)
            
            # Check shipping info for selected orders only
            tracking_info = gbf.get_order_confirmations(order_numbers)
            if tracking_info:
                orders._update_orders_with_shipping_info(tracking_info)
                message = f"Successfully checked shipping status for orders: {', '.join(order_numbers)}"
                self.message_user(request, message, messages.SUCCESS)
            else:
                self.message_user(request, "No shipping information available for the selected orders.", messages.INFO)
                
        except Exception as e:
            logger.error(f"Error checking order status: {str(e)}")
            self.message_user(request, f"Error checking order status: {str(e)}", messages.ERROR)
    
    check_orders_status.short_description = "Check shipping status for selected orders"

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
