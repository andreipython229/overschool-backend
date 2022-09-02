from common_services.mixins import WithHeadersViewSet
from courses.models import Course
from courses.serializers import CourseSerializer
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from common_services.mixins import logging_mixins


class CourseViewSet(viewsets.ModelViewSet, logging_mixins.LoggingMixin):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)
