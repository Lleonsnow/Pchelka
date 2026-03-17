from django.contrib import admin
from .models import Broadcast


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "delivered_count", "error_count", "created_at", "sent_at")
    list_editable = ("status",)
    list_filter = ("status",)
    readonly_fields = ("sent_at", "delivered_count", "error_count")
    actions = ["mark_ready"]

    @admin.action(description="Отметить как «Готово» к отправке")
    def mark_ready(self, request, queryset):
        updated = queryset.filter(status=Broadcast.Status.DRAFT).update(status=Broadcast.Status.READY)
        self.message_user(request, f"Отмечено рассылок: {updated}.")
