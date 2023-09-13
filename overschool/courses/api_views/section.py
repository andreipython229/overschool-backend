from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import (
    BaseLesson,
    Course,
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    UserProgressLogs,
)
from courses.serializers import SectionSerializer
from django.db.models import F
from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

from .schemas.section import SectionsSchemas
from common_services.mixins.order_mixin import generate_order

s = SelectelClient()


@method_decorator(
    name="partial_update",
    decorator=SectionsSchemas.partial_update_schema(),
)
class SectionViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт получения, создания, редактирования и удаления секций.\n
    <h2>/api/{school_name}/sections/</h2>\n
    Разрешения для просмотра секций (любой пользователь)
    Разрешения для создания и изменения секций (только пользователи с группой 'Admin')
    """

    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in ["list", "retrieve", "lessons"]:
            # Разрешения для просмотра секций (любой пользователь школы)
            if user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                Section.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Section.objects.filter(course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return Section.objects.filter(course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return Section.objects.filter(course_id__in=course_ids)

        return Section.objects.none()

    def retrieve(self, request, pk=None, school_name=None):
        queryset = self.get_queryset()
        section = queryset.filter(pk=pk).first()
        if not section:
            return Response("Раздел не найден или у вас нет необходимых прав.")
        serializer = SectionSerializer(section)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        course = self.request.data.get("course")
        if course is not None:
            courses = Course.objects.filter(school__name=school_name)
            try:
                courses.get(pk=course)
            except courses.model.DoesNotExist:
                raise NotFound("Указанный курс не относится к этой школе.")

        order = generate_order(Section)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(order=order)
            return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        course = self.request.data.get("course")
        if course is not None:
            courses = Course.objects.filter(school__name=school_name)
            try:
                courses.get(pk=course)
            except courses.model.DoesNotExist:
                raise NotFound("Указанный курс не относится к этой школе.")

        section = self.get_object()
        serializer = self.get_serializer(section, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        course = instance.course
        school_id = course.school.school_id
        base_lessons_ids = list(
            map(
                lambda el: el["id"],
                list(BaseLesson.objects.filter(section=instance).values("id")),
            )
        )
        remove_resp = None

        # Получаем, а затем удаляем файлы и сегменты всех уроков удаляемого раздела
        for id in base_lessons_ids:
            files_to_delete = s.get_folder_files(
                "{}_school/{}_course/{}_lesson".format(school_id, course.course_id, id)
            )
            segments_to_delete = s.get_folder_files(
                "{}_school/{}_course/{}_lesson".format(school_id, course.course_id, id),
                "_segments",
            )
            if files_to_delete:
                if s.bulk_remove_from_selectel(files_to_delete) == "Error":
                    remove_resp = "Error"
            if segments_to_delete:
                if (
                        s.bulk_remove_from_selectel(segments_to_delete, "_segments")
                        == "Error"
                ):
                    remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True)
    def lessons(self, request, pk, *args, **kwargs):
        """Эндпоинт получения, всех уроков, домашек и тестов секций.\n
        <h2>/api/{school_name}/sections/{section_id}/lessons/</h2>\n
        """
        queryset = self.get_queryset()
        section = queryset.filter(pk=pk)

        data = section.values(
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
            if user.groups.filter(group__name="Admin").exists():
                a = Homework.objects.filter(section=value["section"])
                b = Lesson.objects.filter(section=value["section"])
                c = SectionTest.objects.filter(section=value["section"])
            elif user.groups.filter(group__name__in=["Student", "Teacher", ]).exists():
                a = Homework.objects.filter(section=value["section"], active=True)
                b = Lesson.objects.filter(section=value["section"], active=True)
                c = SectionTest.objects.filter(section=value["section"], active=True)
            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["lessons"].append(
                        {
                            "type": types[i[0]],
                            "section": dict_obj["section"],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                            "baselesson_ptr_id": obj.baselesson_ptr_id,
                            "section_id": obj.section_id,
                            "active": obj.active,
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


SectionViewSet = apply_swagger_auto_schema(
    tags=["sections"], excluded_methods=["partial_update"]
)(SectionViewSet)
