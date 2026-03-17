from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=512)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "faq_faq"
        verbose_name = "Вопрос FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question[:80]
