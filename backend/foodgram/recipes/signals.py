from pathlib import Path

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Recipe


@receiver(post_delete, sender=Recipe)
def image_delete(sender, instance, **kwargs):
    """Удалить картинку при удалении рецепта."""
    path = Path(instance.image.path)
    if path:
        path.unlink()
