from decimal import Decimal

from django.db import models

from apps.catalog.models import Product
from apps.users.models import TelegramUser


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        CONFIRMED = "confirmed", "Подтверждён"
        PAYMENT_PENDING = "payment_pending", "Ожидает оплаты"
        PAID = "paid", "Оплачен"
        SHIPPED = "shipped", "Отправлен"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=32)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders_order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.id} {self.user.telegram_id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "orders_orderitem"
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
