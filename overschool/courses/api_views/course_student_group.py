from common_services.mixins import WithHeadersViewSet
from courses.models import StudentsGroup
from courses.serializers import StudentsGroupCourseSerializer
from rest_framework import permissions, generics


class StudentsGroupCourseViewSet(WithHeadersViewSet, generics.ListAPIView):
    serializer_class = StudentsGroupCourseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        course_id = self.request.GET.get("course_id")
        if course_id:
            queryset = StudentsGroup.objects.filter(course_id=course_id)
            return queryset
        queryset = StudentsGroup.objects.all()
        return queryset
