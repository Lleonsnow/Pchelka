from django.db import models


class SubscriptionChannel(models.Model):
    """Канал или группа, на которую пользователь должен подписаться."""
    channel_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255, blank=True)
    invite_link = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "bot_settings_subscriptionchannel"
        verbose_name = "Канал подписки"
        verbose_name_plural = "Каналы подписки"
        ordering = ["order"]

    def __str__(self):
        return self.title or str(self.channel_id)


class BotSettings(models.Model):
    """Синглтон-настройки бота (один объект)."""
    admin_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID группы/чата для уведомлений о заказах и управления статусами",
    )
    admin_telegram_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Список telegram_id админов (для команды /orders и смены статуса из чата)",
    )

    class Meta:
        db_table = "bot_settings_botsettings"
        verbose_name = "Настройки бота"
        verbose_name_plural = "Настройки бота"

    def __str__(self):
        return "Настройки бота"
