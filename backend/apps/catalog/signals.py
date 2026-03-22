from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.api.cache import bump_public_api_cache
from apps.catalog.models import Category, Product, ProductImage


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
@receiver(post_save, sender=ProductImage)
@receiver(post_delete, sender=ProductImage)
def _invalidate_catalog_api_cache(**kwargs) -> None:
    bump_public_api_cache()
