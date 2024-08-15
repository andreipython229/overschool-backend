from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import (
    BaseLesson,
    Lesson,
    LessonAvailability,
    LessonEnrollment,
    Section,
    StudentsGroup,
    Course
)
from courses.serializers import (
    LessonAvailabilitySerializer,
    LessonDetailSerializer,
    LessonEnrollmentSerializer,
    LessonSerializer,
    LessonUpdateSerializer,
)
from courses.services import LessonProgressMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import School
from schools.school_mixin import SchoolMixin

User = get_user_model()

s3 = UploadToS3()


class LessonAvailabilityViewSet(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
    queryset = LessonAvailability.objects.all()
    serializer_class = LessonAvailabilitySerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student_ids = request.data.get("student_ids")
        lesson_data = request.data.get("lesson_data")

        if student_ids is None or lesson_data is None:
            return Response(
                {"error": "Недостаточно данных для выполнения запроса."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for student_id in student_ids:
                for lesson_info in lesson_data:
                    lesson_id = lesson_info.get("lesson_id")
                    available = lesson_info.get("available")
                    if lesson_id is not None and available is not None:
                        existing_availability = LessonAvailability.objects.filter(
                            student_id=student_id, lesson_id=lesson_id, available=False
                        )
                        if available and existing_availability.exists():
                            existing_availability.delete()
                        elif not available:
                            LessonAvailability.objects.update_or_create(
                                student_id=student_id,
                                lesson_id=lesson_id,
                                defaults={"available": available},
                            )

        return Response(
            {"success": "Доступность уроков обновлена."}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["POST"])
    def reset_to_group(self, request, *args, **kwargs):
        group_id = request.data.get("group_id")
        student_id = request.data.get("student_id")
        if not group_id or not student_id:
            return Response(
                {"error": "group_id и student_id обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_group = StudentsGroup.objects.filter(pk=group_id).first()

        if not student_group.students.filter(pk=student_id).exists():
            return Response(
                {"error": "Указанный студент не учится в указанной группе"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lessons = BaseLesson.objects.filter(section__course=student_group.course_id)
        for lesson in lessons:
            available = lesson.is_available_for_group(student_group)
            existing_restriction = LessonAvailability.objects.filter(
                student_id=student_id, lesson=lesson, available=False
            )
            if available and existing_restriction.exists():
                existing_restriction.delete()
            elif not available:
                LessonAvailability.objects.update_or_create(
                    student_id=student_id,
                    lesson=lesson,
                    defaults={"available": available},
                )

        return Response(
            {"success": "Доступы студента к урокам обновлены до групповых."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        student_id = self.kwargs.get("student_id")
        lesson_availabilities = LessonAvailability.objects.filter(
            student_id=student_id, available=False
        )

        lessons_data = []
        for lesson_availability in lesson_availabilities:
            lessons_data.append(
                {
                    "lesson_id": lesson_availability.lesson.id,
                    "available": lesson_availability.available,
                }
            )

        return Response(lessons_data)


class LessonEnrollmentViewSet(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
    queryset = LessonEnrollment.objects.all()
    serializer_class = LessonEnrollmentSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student_group_id = request.data.get("student_group_id")
        lesson_data = request.data.get("lesson_data")

        if student_group_id is None or not lesson_data:
            return Response(
                {"error": "Недостаточно данных для выполнения запроса."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for lesson_info in lesson_data:
                lesson_id = lesson_info.get("lesson_id")
                available = lesson_info.get("available")

                if lesson_id is not None and available is not None:
                    if available:
                        LessonEnrollment.objects.filter(
                            student_group_id=student_group_id, lesson_id=lesson_id
                        ).delete()
                    else:
                        LessonEnrollment.objects.update_or_create(
                            student_group_id=student_group_id, lesson_id=lesson_id
                        )

        return Response(
            {"success": "Доступность уроков для группы студентов обновлена."},
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        student_group_id = request.data.get("student_group_id")

        if student_group_id is None:
            return Response(
                {"error": "Недостаточно данных для выполнения запроса."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lesson_enrollments = LessonEnrollment.objects.filter(
            student_group_id=student_group_id
        )
        serializer = LessonEnrollmentSerializer(lesson_enrollments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LessonViewSet(
    LoggingMixin,
    WithHeadersViewSet,
    LessonProgressMixin,
    SchoolMixin,
    viewsets.ModelViewSet,
):
    """Эндпоинт на получение, создания, изменения и удаления уроков\n
    <h2>/api/{school_name}/lessons/</h2>\n
    Разрешения для просмотра уроков (любой пользователь) \n Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')"""

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра уроков (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        else:
            return LessonSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()  # Возвращаем пустой queryset при генерации схемы

        user = self.request.user
        school_name = self.kwargs.get("school_name")

        try:
            school_id = School.objects.get(name=school_name).school_id
        except School.DoesNotExist:
            return Response({"error": "School not found"}, status=status.HTTP_404_NOT_FOUND)

        course_id = self.request.GET.get('courseId')

        if course_id:
            try:
                course = Course.objects.get(course_id=course_id)
                if course.is_copy:
                    original_course = Course.objects.get(name=course.name, is_copy=False)
                    return Lesson.objects.filter(section__course=original_course)
                else:
                    return Lesson.objects.filter(section__course=course)
            except Course.DoesNotExist:
                return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return Lesson.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, students=user
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(active=True, section__course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher", school=school_id).exists():
            course_ids = StudentsGroup.objects.filter(
                course_id__school__name=school_name, teacher_id=user.pk
            ).values_list("course_id", flat=True)
            return Lesson.objects.filter(active=True, section__course_id__in=course_ids)

        return Lesson.objects.none()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        section = self.request.data.get("section")
        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится ни к одному курсу этой школы."
                )

        serializer = LessonSerializer(data={**request.data})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        section = self.request.data.get("section")

        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound(
                    "Указанная секция не относится не к одному курсу этой школы."
                )
        instance = self.get_object()
        serializer = LessonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.data.get("active"):
            serializer.validated_data["active"] = instance.active

        instance.save()
        self.perform_update(serializer)

        serializer = LessonDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        files_to_delete = list(
            map(
                lambda el: str(el["file"]),
                list(instance.text_files.values("file"))
                + list(instance.audio_files.values("file")),
            )
        )
        blocks_video_to_delete = list(
            map(
                lambda el: str(el["video"]),
                list(
                    filter(
                        lambda el: el["video"] != "", instance.blocks.values("video")
                    )
                ),
            )
        )
        blocks_picture_to_delete = list(
            map(
                lambda el: str(el["picture"]),
                list(
                    filter(
                        lambda el: el["picture"] != "",
                        instance.blocks.values("picture"),
                    )
                ),
            )
        )
        files_to_delete += blocks_video_to_delete
        files_to_delete += blocks_picture_to_delete

        remove_resp = None
        objects_to_delete = [{"Key": key} for key in files_to_delete]
        if files_to_delete:
            if s3.delete_files(objects_to_delete) == "Error":
                remove_resp = "Error"

        self.perform_destroy(instance)
        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


class LessonUpdateViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, generics.GenericAPIView
):
    serializer_class = None

    @swagger_auto_schema(method="post", request_body=LessonUpdateSerializer)
    @action(detail=False, methods=["POST"])
    def shuffle_lessons(self, request, *args, **kwargs):

        data = request.data

        # сериализатор с полученными данными
        serializer = LessonUpdateSerializer(data=data, many=True)

        if serializer.is_valid():
            BaseLesson.disable_constraint("unique_section_lesson_order")
            for lesson_data in serializer.validated_data:
                baselesson_ptr_id = lesson_data["baselesson_ptr_id"]
                new_order = lesson_data["order"]

                # Обновите порядок урока в базе данных
                try:
                    lesson = BaseLesson.objects.get(id=baselesson_ptr_id)
                    lesson.order = new_order
                    lesson.save()
                except Exception as e:
                    BaseLesson.enable_constraint()
                    return Response(str(e), status=500)

            BaseLesson.enable_constraint()
            return Response("Уроки успешно обновлены", status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
