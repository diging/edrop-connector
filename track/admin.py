from django.contrib import admin
from track.models import *

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ["record_id", "initiated_by", "tracking_nr"]


admin.site.register(Order, OrderAdmin)