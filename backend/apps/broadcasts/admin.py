from django.contrib import admin
from django.utils.html import format_html
from .models import Broadcast


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status_badge",
        "delivered_count",
        "error_count",
        "created_at",
        "sent_at",
    )
    list_filter = ("status",)
    readonly_fields = ("sent_at", "delivered_count", "error_count")
    actions = ["mark_ready"]
    list_per_page = 25

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj: Broadcast):
        code = (obj.status or "").replace("_", "-")
        return format_html(
            '<span class="status-badge status-{}">{}</span>',
            code,
            obj.get_status_display(),
        )

    @admin.action(description="Отметить как «Готово» к отправке")
    def mark_ready(self, request, queryset):
        updated = queryset.filter(status=Broadcast.Status.DRAFT).update(status=Broadcast.Status.READY)
        self.message_user(request, f"Отмечено рассылок: {updated}.")
