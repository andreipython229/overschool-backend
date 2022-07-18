import datetime
from rest_framework import status
from rest_framework import viewsets
from rest_framework import views
from users.models import SchoolUser
from users.serializers import SchoolUserSerializer
from users.services import SenderServiceMixin
import redis
from django.conf import settings
from rest_framework.response import Response
import secrets
from rest_framework import permissions


class SchoolUserViewSet(viewsets.ModelViewSet):
    queryset = SchoolUser.objects.all()
    serializer_class = SchoolUserSerializer


class RegisterView(views.APIView,
                   SenderServiceMixin):
    """
    Вьюха для регистрации со стороны админа
    """
    permission_classes = (permissions.AllowAny,)  # далее можно изменить

    def post(self, request):
        """
        Функция для отправки регистрационной ссылки пользоваелю, ответы требуют доработки
        """
        sender_type = request.data.get('sender_type')
        if sender_type == "mail":
            result = self.send_code_by_email(request.data.get('recipient'),
                                             request.data.get('user_type'))
        else:
            result = self.send_code_by_phone(request.data.get('recipient'),
                                             request.data.get('user_type'))
        if result:
            return Response({"result": "OK", "message": "Всё прошло хорошо, сообщение отправлено"},
                            status=status.HTTP_200_OK)
        else:
            return Response({"result": "Error", "message": "Что-то пошло не так"}, status=status.HTTP_400_BAD_REQUEST)


