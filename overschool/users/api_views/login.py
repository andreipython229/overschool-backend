from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import login
from rest_framework import permissions, views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.serializers import LoginSerializer


class LoginView(LoggingMixin, WithHeadersViewSet, views.APIView):
    """<h2>/api/login/</h2>\n"""

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        login(request, user)

        tokens = serializer.create(serializer.validated_data)

        return Response(tokens)
