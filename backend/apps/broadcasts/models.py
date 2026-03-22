from django.db import models


class BroadcastTemplate(models.Model):
    """Текст и картинка для быстрой отправки (админка и админ-чат бота)."""

    name = models.CharField("Название", max_length=128)
    text = models.TextField("Текст (HTML как в Telegram)")
    image = models.ImageField(
        "Картинка",
        upload_to="broadcast_templates/%Y/%m/",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField("Активен", default=True)
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "broadcasts_broadcasttemplate"
        verbose_name = "Шаблон рассылки"
        verbose_name_plural = "Шаблоны рассылок"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class Broadcast(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        READY = "ready", "Готово"
        SENT = "sent", "Отправлено"

    text = models.TextField()
    image = models.ImageField(upload_to="broadcasts/%Y/%m/", null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "broadcasts_broadcast"
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Рассылка #{self.id} ({self.status})"
