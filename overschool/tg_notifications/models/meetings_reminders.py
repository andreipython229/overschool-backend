from django.db import models
from schools.models import SchoolMeetings


class MeetingsRemindersTG(models.Model):
    meeting = models.ForeignKey(SchoolMeetings, on_delete=models.CASCADE, null=True, blank=True)
    daily = models.BooleanField(default=False)
    in_three_hours = models.BooleanField(default=False)
    ten_minute = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
