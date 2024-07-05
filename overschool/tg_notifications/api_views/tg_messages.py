from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework import viewsets

from schools.models import School
from courses.models.courses.course import Course
from courses.models.students.students_group import StudentsGroup
from ..models import TgUsers
from ..serializers import SendMessageSerializer
from .bot import BotNotifications


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