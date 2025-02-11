from django.contrib import admin
from track.models import *

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ["record_id", "order_number", "tracking_nrs", "return_tracking_nrs", "tube_serials", "order_status", "ship_date"]

class ConfirmationCheckLogAdmin(admin.ModelAdmin):
    list_display = ["id", "start_time", "end_time", "is_complete"]
    fields = ("job_id", "apscheduler", "orders", "gbf", "redcap", "end_time", "is_complete")

class OrderLogAdmin(admin.ModelAdmin):
    list_display = ["id", "order_number", "start_time", "end_time", "is_complete"]
    fields = ("order_number", "redcap", "orders", "gbf", "end_time", "is_complete")

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLog, OrderLogAdmin)
admin.site.register(ConfirmationCheckLog, ConfirmationCheckLogAdmin)
