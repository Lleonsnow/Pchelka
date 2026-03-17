from django.db import models

from apps.catalog.models import Product
from apps.users.models import TelegramUser


class Cart(models.Model):
    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.user_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_cartitem"
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        unique_together = [("cart", "product")]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
