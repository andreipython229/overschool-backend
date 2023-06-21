from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Homework, Lesson, Section, SectionTest, UserProgressLogs
from courses.serializers import SectionSerializer
from django.db.models import F
from django.forms.models import model_to_dict
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


class SectionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт получения, создания, редактирования и удаления секций.\n
    Разрешения для просмотра секций (любой пользователь)
    Разрешения для создания и изменения секций (только пользователи с группой 'Admin')
    """

    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра секций (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения секций (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(group__name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    @action(detail=True)
    def lessons(self, request, pk, *args, **kwargs):
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
        user = self.request.user
        lesson_progress = UserProgressLogs.objects.filter(user_id=user.pk)
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            a = Homework.objects.filter(section=value["section"])
            b = Lesson.objects.filter(section=value["section"])
            c = SectionTest.objects.filter(section=value["section"])
            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["lessons"].append(
                        {
                            "type": types[i[0]],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                            "viewed": lesson_progress.filter(
                                lesson_id=obj.baselesson_ptr_id, viewed=True
                            ).exists(),
                            "completed": lesson_progress.filter(
                                lesson_id=obj.baselesson_ptr_id, completed=True
                            ).exists(),
                        }
                    )
            result_data["lessons"].sort(key=lambda x: x["order"])

        return Response(result_data)
