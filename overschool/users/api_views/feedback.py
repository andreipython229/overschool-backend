from rest_framework import generics
from users.models.feedback import Feedback
from users.serializers.feedback import FeedbackSerializer

class FeedbackListCreateView(generics.ListCreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer