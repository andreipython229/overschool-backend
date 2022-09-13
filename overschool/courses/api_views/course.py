from common_services.mixins import WithHeadersViewSet
from courses.models import Course, Section
from courses.serializers import CourseSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common_services.mixins import logging_mixins


class CourseViewSet(viewsets.ModelViewSet, logging_mixins.LoggingMixin):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True)
    def sections(self, request, pk):
        course = self.get_object()

        sections = Section.objects.filter(course_id=course.pk).order_by("section_id")

        all_data = {}
        for section in sections:
            courses = f"{course.pk}"
            if courses in all_data.keys():
                all_data[courses].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

            else:
                all_data[courses] = []
                all_data[courses].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

        return Response(all_data)
