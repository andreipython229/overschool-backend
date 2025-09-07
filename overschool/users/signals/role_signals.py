from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


@receiver(post_save)
def assign_admin_role(sender, instance, created, **kwargs):
    """Назначение роли администратора при создании школы"""
    if sender.__name__ == 'School' and created:
        try:
            from django.contrib.auth.models import Group
            from .models import UserGroup

            admin_group, _ = Group.objects.get_or_create(name="Admin")
            if hasattr(instance, 'owner'):
                UserGroup.objects.get_or_create(
                    user=instance.owner,
                    group=admin_group,
                    school=instance
                )
        except Exception as e:
            logger.error(f"Admin role assignment failed for school {instance.pk}: {e}")