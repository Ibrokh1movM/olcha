from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New product created: {instance.name} by {instance.created_at}")
    else:
        logger.info(f"Product updated: {instance.name} at {instance.updated_at}")
