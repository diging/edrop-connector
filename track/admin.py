from django.contrib import admin
from track.models import *

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ["record_id", "initiated_by", "tracking_nrs", "order_status", "ship_date"]

class ConfirmationCheckLogAdmin(admin.ModelAdmin):
    list_display = ["id", "start_time", "end_time", "is_complete"]

class OrderLogAdmin(admin.ModelAdmin):
    list_display = ["id", "order_number", "start_time", "end_time", "is_complete"]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLog, OrderLogAdmin)
admin.site.register(ConfirmationCheckLog, ConfirmationCheckLogAdmin)
