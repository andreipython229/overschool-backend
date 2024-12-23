from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    BaseLesson,
    Course,
    CourseCopy,
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    StudentsGroupSettings,
    UserHomework,
    UserProgressLogs,
    UserTest,
)
from courses.serializers import (
    SectionOrderSerializer,
    SectionRetrieveSerializer,
    SectionSerializer,
)
from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

from .schemas.section import SectionsSchemas

s3 = UploadToS3()


@method_decorator(
    name="partial_update",
    decorator=SectionsSchemas.partial_update_schema(),
)
class SectionViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
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
            if (
                user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
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

        def get_original_course_ids(course_ids):
            original_course_ids = CourseCopy.objects.filter(
                course_copy_id__in=course_ids
            ).values_list("course_id", flat=True)

            original_courses = Course.objects.filter(
                Q(course_id__in=original_course_ids)
                | Q(course_id__in=course_ids, is_copy=False)
            ).values_list("course_id", flat=True)

            return original_courses

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Section.objects.filter(course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            original_course_ids = get_original_course_ids(course_ids)
            return Section.objects.filter(course_id__in=original_course_ids)

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
        context = {"request": request}
        serializer = SectionRetrieveSerializer(section, context=context)
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

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
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
            files_to_delete = s3.get_list_objects(
                "{}_school/{}_course/{}_lesson".format(school_id, course.course_id, id)
            )

            if files_to_delete:
                if s3.delete_files(files_to_delete) == "Error":
                    remove_resp = "Error"

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, url_path="lessons/(?P<courseId>[^/.]+)")
    def lessons(self, request, pk, *args, **kwargs):
        """Эндпоинт получения, всех уроков, домашек и тестов секций.\n
        <h2>/api/{school_name}/sections/{section_id}/lessons/</h2>\n
        """
        queryset = self.get_queryset()
        course_id = kwargs["courseId"]
        section = queryset.filter(pk=pk)
        section_obj = section.first()

        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        course = Course.objects.get(course_id=int(course_id))

        data = section.values(
            section_name=F("name"),
            section=F("section_id"),
        )
        result_data = dict(
            section_name=data[0]["section_name"],
            section_id=data[0]["section"],
        )

        group = None
        if user.groups.filter(group__name="Student", school=school).exists():
            try:
                group = StudentsGroup.objects.get(students=user, course_id_id=course_id)
                if course.is_copy and course.public != "О":
                    return Response(
                        {
                            "error": "Доступ к курсу временно заблокирован. Обратитесь к администратору"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                elif not course.is_copy and section_obj.course.public != "О":
                    return Response(
                        {
                            "error": "Доступ к курсу временно заблокирован. Обратитесь к администратору"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except Exception:
                raise NotFound("Ошибка поиска группы пользователя.")
        elif user.groups.filter(group__name="Teacher", school=school).exists():
            try:
                group = StudentsGroup.objects.get(
                    teacher_id=user.pk, course_id_id__sections=pk
                )
            except Exception:
                raise NotFound("Ошибка поиска группы пользователя.")
        if group:
            result_data["group_settings"] = {
                "task_submission_lock": group.group_settings.task_submission_lock,
                "strict_task_order": group.group_settings.strict_task_order,
                "submit_homework_to_go_on": group.group_settings.submit_homework_to_go_on,
                "submit_test_to_go_on": group.group_settings.submit_test_to_go_on,
                "success_test_to_go_on": group.group_settings.success_test_to_go_on,
            }
            result_data["group_id"] = group.group_id

        result_data["lessons"] = []

        lesson_progress = UserProgressLogs.objects.filter(user_id=user.pk)
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            if user.groups.filter(group__name="Admin", school=school).exists():
                a = Homework.objects.filter(section=value["section"])
                b = Lesson.objects.filter(section=value["section"])
                c = SectionTest.objects.filter(section=value["section"])
            elif user.groups.filter(
                group__name__in=[
                    "Student",
                    "Teacher",
                ],
                school=school,
            ).exists():
                a = Homework.objects.filter(section=value["section"], active=True)
                b = Lesson.objects.filter(section=value["section"], active=True)
                c = SectionTest.objects.filter(section=value["section"], active=True)
                if user.groups.filter(group__name="Student", school=school).exists():
                    a = a.exclude(lessonavailability__student=user)
                    b = b.exclude(lessonavailability__student=user)
                    c = c.exclude(lessonavailability__student=user)

            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    sended = None
                    if obj in a:
                        sended = UserHomework.objects.filter(
                            homework=obj, user=user
                        ).exists()
                    if obj in c:
                        sended = UserTest.objects.filter(test=obj, user=user).exists()
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
                            "sended": sended,
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


class SectionUpdateViewSet(WithHeadersViewSet, SchoolMixin, generics.GenericAPIView):
    serializer_class = None

    @swagger_auto_schema(method="post", request_body=SectionOrderSerializer)
    @action(detail=False, methods=["POST"])
    def shuffle_sections(self, request, *args, **kwargs):

        data = request.data

        # сериализатор с полученными данными
        serializer = SectionOrderSerializer(data=data, many=True)

        if serializer.is_valid():
            for section_data in serializer.validated_data:
                section_id = section_data["section_id"]
                new_order = section_data["order"]

                # Обновите порядок секции в базе данных
                try:
                    section = Section.objects.get(section_id=section_id)
                    section.order = new_order
                    section.save()
                except Exception as e:
                    return Response(str(e), status=500)
            return Response("Секции успешно обновлены", status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
