from django.db import models
from courses.models import StudentsGroup


class MeetingsReminders(models.Model):

    group = models.ForeignKey(StudentsGroup, on_delete=models.CASCADE)
    event_time = models.DateTimeField()
    daily = models.BooleanField(default=False)
    hourly = models.BooleanField(default=False)
    half_hourly = models.BooleanField(default=False)
    ten_minute = models.BooleanField(default=False)

    def __str__(self):
        return f"Напоминание для группы {self.group}. Начало видеоконференции в {self.event_time}"

    # def send_message_to_users(self):
    #     from ..models import TgUsers
    #     from ..views import BotNotifications
    #     from courses.models import StudentsGroup
    #
    #     try:
    #         print('дошло')
    #         message = f"Reminder for group {self.group} at {self.event_time}"
    #         print(message)
    #         students = StudentsGroup.objects.filter(students=self.group.group_id)
    #         # kek = [student.id for student in students]
    #         print(students)
    #         for student in students:
    #             try:
    #                 tg_user = TgUsers.objects.get(user_id=student).tg_user_id
    #
    #                 BotNotifications.send_notifications(
    #                     tg_user.chat_id,
    #                     message
    #                 )
    #
    #             except TgUsers.DoesNotExist:
    #                 pass
    #     except Exception as e:
    #         print(e)