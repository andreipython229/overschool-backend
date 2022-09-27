from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Section, Lesson
from courses.serializers import SectionSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class SectionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    @action(detail=True)
    def lessons(self, request, pk):
        section = self.get_object()

        lessons = Lesson.objects.filter(section_id=section.pk).order_by("order")

        all_data = {}

        less = "lessons"
        all_data["section_id"] = f"{section.pk}"
        for lesson in lessons:
            if less in all_data.keys():
                all_data[less].append(
                    {
                        "name": lesson.name,
                        "lesson_id": lesson.lesson_id,
                        "description": lesson.description,
                        "video": lesson.video,
                        "code": lesson.code,
                        "file": str(lesson.file),
                        "homeworks": lesson.homeworks.values().order_by("order"),
                        "tests": lesson.lessons.values().order_by("order"),
                    }
                )
            else:
                all_data[less] = []
                all_data[less].append(
                    {
                        "name": lesson.name,
                        "lesson_id": lesson.lesson_id,
                        "description": lesson.description,
                        "video": lesson.video,
                        "code": lesson.code,
                        "file": str(lesson.file),
                        "homeworks": lesson.homeworks.values().order_by("order"),
                        "tests": lesson.lessons.values().order_by("order"),
                    }
                )

        return Response(all_data)
