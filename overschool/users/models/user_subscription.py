from django.db import models
from schools.models import School
from users.models import User


class UserSubscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    subscription_id = models.CharField(max_length=255)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="subscriptions"
    )

    def __str__(self):
        return f"{self.user} - {self.subscription_id} - {self.school}"

    class Meta:
        unique_together = ("user", "school")
