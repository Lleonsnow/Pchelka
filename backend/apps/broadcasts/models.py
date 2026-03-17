from django.db import models


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
