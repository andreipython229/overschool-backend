from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

@receiver(post_save)
def create_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля для нового пользователя"""
    if sender.__name__ == 'User' and created:
        try:
            from .models import Profile
            Profile.objects.get_or_create(user=instance)
        except Exception as e:
            logger.error(f"Profile creation failed for user {instance.pk}: {e}")

@receiver(post_save)
def save_profile(sender, instance, **kwargs):
    """Автоматическое сохранение профиля при обновлении пользователя"""
    if sender.__name__ == 'User':
        try:
            instance.profile.save()
        except (ObjectDoesNotExist, AttributeError) as e:
            logger.warning(f"Profile save failed for user {instance.pk}: {e}")

