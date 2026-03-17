from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=128, blank=True)
    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_telegramuser"
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        return f"{self.telegram_id} (@{self.username or '—'})"
