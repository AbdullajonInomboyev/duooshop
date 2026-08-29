from django.contrib import admin
from .models import DeliveryRoute, DeliveryStop


class DeliveryStopInline(admin.TabularInline):
    model = DeliveryStop
    extra = 0


@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ("courier", "date", "is_closed", "created_at")
    list_filter = ("date", "is_closed", "courier")
    inlines = [DeliveryStopInline]


@admin.register(DeliveryStop)
class DeliveryStopAdmin(admin.ModelAdmin):
    list_display = ("order", "route", "sequence", "is_delivered", "collected_amount")
    list_filter = ("is_delivered", "route__date")
