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
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        sender_type = request.data.get('sender_type')
        if sender_type == "mail":
            result = self.send_code_by_email(request.data.get('recipient'))
        else:
            result = self.send_code_by_phone(request.data.get('recipient'))
        if result:
            return Response({"result": "Хайпим"}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "Не Хайпим("}, status=status.HTTP_400_BAD_REQUEST)


