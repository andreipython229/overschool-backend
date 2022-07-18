from courses.models import Course
from courses.serializers import CourseSerializer
from rest_framework import permissions, viewsets


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
