from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Lesson
from courses.serializers import LessonSerializer


class LessonViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def retrieve(self, request, *args, **kwargs):
        lesson_id = self.kwargs["pk"]

        try:
            instance = Lesson.objects.get(lesson_id=lesson_id)
            serializer = self.get_serializer(instance)
            return Response(serializer.data | {"type": "lesson"})
        except ObjectDoesNotExist:
            return Response(
                {"status": "Error", "message": "Not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
