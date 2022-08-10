from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from users.models import Profile, User


@receiver(post_save, sender=User)
def create_users_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user_ptr=instance)


@receiver(post_delete, sender=User)
def delete_users_profile(sender, instance, **kwargs):
    Profile.objects.filter(user_ptr=instance).delete()
