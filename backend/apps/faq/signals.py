from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.api.cache import bump_public_api_cache
from apps.faq.models import FAQ


@receiver(post_save, sender=FAQ)
@receiver(post_delete, sender=FAQ)
def _invalidate_faq_api_cache(**kwargs) -> None:
    bump_public_api_cache()
