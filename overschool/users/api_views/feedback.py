from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Feedback
from users.serializers import FeedbackSerializer


class FeedbackViewSet(APIView):
    """
    API для просмотра списка отзывов о платформе.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Возвращает список всех отзывов.
        """
        feedbacks = Feedback.objects.all()
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
