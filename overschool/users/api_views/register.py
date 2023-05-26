from common_services.mixins import WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import generics, permissions
from users.serializers import SignupSerializer
from users.services import JWTHandler

User = get_user_model()
jwt_handler = JWTHandler()


class SignupView(WithHeadersViewSet, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = HttpResponse("http://127.0.0.1:8000/api/users/", status=201)
        return response
