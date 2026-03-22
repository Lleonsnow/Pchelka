from decimal import Decimal

from django.contrib import admin
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html
from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id",
        "username",
        "phone",
        "first_name",
        "orders_count",
        "orders_total",
        "created_at",
    )
    search_fields = ("telegram_id", "username", "phone")
    readonly_fields = ("created_at", "updated_at", "orders_count", "orders_total", "orders_history")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _orders_count=Count("orders", distinct=True),
            _orders_total=Coalesce(
                Sum("orders__total"),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

    @admin.display(description="Заказов")
    def orders_count(self, obj: TelegramUser) -> int:
        return getattr(obj, "_orders_count", 0) or 0

    @admin.display(description="Сумма заказов")
    def orders_total(self, obj: TelegramUser) -> str:
        total = getattr(obj, "_orders_total", 0) or 0
        return f"{total} ₽"

    @admin.display(description="История заказов")
    def orders_history(self, obj: TelegramUser):
        orders = obj.orders.order_by("-created_at")[:20]
        if not orders:
            return "Заказов нет"

        links: list[str] = []
        for order in orders:
            url = reverse("admin:orders_order_change", args=[order.id])
            links.append(
                format_html(
                    '<a href="{}">#{}</a> - {} - {} ₽',
                    url,
                    order.id,
                    order.get_status_display(),
                    order.total,
                )
            )
        return format_html("<br>".join(links))
