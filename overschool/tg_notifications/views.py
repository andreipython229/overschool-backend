import telebot
import os

from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework import viewsets

from courses.models.courses.course import Course
from courses.models.students.students_group import StudentsGroup
from .models import Notifications, TgUsers
from .serializers import NotificationsSerializer, SendMessageSerializer
from schools.models import School
from django.utils import timezone


bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class BotNotifications:

    @staticmethod
    def send_notifications(tg_user_id, notifications):
        bot.send_message(
            chat_id=tg_user_id,
            text=notifications
        )


class NotificationsViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationsSerializer

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                TgUsers.objects.none()
            )
        user = self.request.user
        queryset = Notifications.objects.filter(tg_user_id__user_id=user)
        return queryset

    class Meta:
        model = Notifications


# class MeetingsRemindersViewSet(viewsets.ModelViewSet):
#     queryset = MeetingsRemindersTG.objects.all()
#     serializer_class = MeetingsRemindersSerializer
#
#     def perform_create(self, serializer):
#         from .tasks import schedule_reminders
#         reminder = serializer.save()
#         print("Reminder ID:", reminder.id)
#         schedule_reminders.apply_async((reminder.id,), eta=timezone.now())
#         print("Task scheduled successfully")


class SendMessageViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendMessageSerializer

    @action(detail=False, methods=['post'], url_path='send-message')
    def send_message(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            students_groups = serializer.validated_data['students_groups']

            user = self.request.user
            for group_id in students_groups:
                course = StudentsGroup.objects.get(group_id=group_id).course_id_id
                school = Course.objects.get(course_id=course).school_id

                if School.objects.filter(school_id=school, owner_id=user).exists():

                    students_list = StudentsGroup.objects.filter(group_id=group_id).values_list('students', flat=True),
                    students = [student_id for queryset in students_list for student_id in queryset]

                    for student_id in students:
                        try:
                            tg_chat_id = TgUsers.objects.get(user_id=student_id).tg_user_id
                            BotNotifications.send_notifications(tg_chat_id, message)
                        except:
                            pass
                    return Response({'status': 'Уведомления отправлены', 'tg_chats_ids': students}, status=status.HTTP_200_OK)

                else:
                    raise PermissionDenied('У вас недостаточно прав для выполнения действия')
        else:
            return Response({'status': 'error', 'message': 'Укажите сообщение и группу/ы'},
                            status=status.HTTP_400_BAD_REQUEST)


