from rest_framework import permissions
from rest_framework import viewsets

from ..models import MeetingsRemindersTG
from ..serializers import MeetingsRemindersSerializer


class MeetingReminderViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingsRemindersSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MeetingsRemindersTG.objects.all()
        return queryset
