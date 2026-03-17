from django.contrib import admin
from .models import Broadcast


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "delivered_count", "error_count", "created_at", "sent_at")
    list_filter = ("status",)
    readonly_fields = ("sent_at", "delivered_count", "error_count")
