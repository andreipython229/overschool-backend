from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Section, Lesson
from homeworks.models import Homework
from lesson_tests.models import LessonTest
from django.db.models import F
from django.forms.models import model_to_dict
from courses.serializers import SectionSerializer

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class SectionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    # permission_classes = [permissions.DjangoModelPermissions]

    @action(detail=True)
    def lessons(self, request, pk):
        section = self.get_object()
        queryset = Section.objects.filter(section_id=section.pk)
        data = queryset.values(
            section_name=F("name"),
            section=F("section_id"),
        )
        result_data = dict(
            section_name=data[0]["section_name"],
            section_id=data[0]["section"],
            lessons=[],
        )
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            a = Homework.objects.filter(section=value["section"])
            b = Lesson.objects.filter(section=value["section"])
            c = LessonTest.objects.filter(section=value["section"])
            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["lessons"].append(
                        {
                            "type": types[i[0]],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                        }
                    )
            result_data["lessons"].sort(key=lambda x: x["order"])

        return Response(result_data)
