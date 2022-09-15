from common_services.mixins import WithHeadersViewSet
from courses.models import Course, Section, Lesson
from courses.serializers import CourseSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


class CourseViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("order")
    serializer_class = CourseSerializer
    permission_classes = (AllowAny,)

    @action(detail=True)
    def sections(self, request, pk):
        course = self.get_object()

        sections = Section.objects.filter(course_id=course.pk).order_by("order")

        all_data = {}

        sect = "sections"
        all_data["course_id"] = f"{course.pk}"
        for section in sections:
            if sect in all_data.keys():
                all_data[sect].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

            else:
                all_data[sect] = []
                all_data[sect].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

        return Response(all_data)

    @action(detail=True)
    def clone(self, request, pk):
        course = self.get_object()
        course_copy = course.make_clone(attrs={'name': f'{course.name}-копия'})
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())
