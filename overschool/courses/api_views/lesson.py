from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_file
from courses.models import BaseLesson, Lesson, Section, Course, StudentsGroup
from courses.serializers import LessonDetailSerializer, LessonSerializer
from courses.services import LessonProgressMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from schools.school_mixin import SchoolMixin
from rest_framework.exceptions import NotFound
from schools.models import School

class LessonViewSet(
    LoggingMixin, WithHeadersViewSet, LessonProgressMixin, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт на получение, создания, изменения и удаления уроков\n
    Разрешения для просмотра уроков (любой пользователь)\n
    Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')"""

    queryset = Lesson.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра уроков (любой пользователь школы)
            if user.groups.filter(group__name__in=["Student", "Teacher"], school=school_id).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')
            if user.groups.filter(group__name="Admin", school=school_id).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        else:
            return LessonSerializer

    def get_queryset(self):
        user = self.request.user

        school_name = self.kwargs.get("school_name")
        if not school_name:
            return Lesson.objects.none()

        if user.groups.filter(group__name="Admin"):
            return Lesson.objects.filter(section__course__school__name=school_name)

        if user.groups.filter(group__name="Student"):
            course_ids = StudentsGroup.objects.filter(course_id__school__name=school_name,
                                                      students=user).values_list("course_id", flat=True)
            return Lesson.objects.filter(section__course_id__in=course_ids)

        if user.groups.filter(group__name="Teacher"):
            course_ids = StudentsGroup.objects.filter(course_id_id__school__name=school_name,
                                                      teacher_id=user.pk).values_list("course_id", flat=True)
            return Lesson.objects.filter(section__course_id__in=course_ids)

        return Lesson.objects.none()

    def retrieve(self, request, pk=None, school_name=None):
        queryset = self.get_queryset()
        lesson = queryset.filter(pk=pk).first()
        if not lesson:
            return Response("Урок не найден.")
        serializer = LessonDetailSerializer(lesson)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")

        section = self.request.data.get("section")
        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound("Указанная секция не относится не к одному курсу этой школы.")

        serializer = LessonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save(video=None)

        if request.FILES.get("video"):
            base_lesson = BaseLesson.objects.get(lessons=lesson)
            video = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
            lesson.video = video
            lesson.save()
            serializer = LessonDetailSerializer(lesson)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")

        section = self.request.data.get("section")

        if section is not None:
            sections = Section.objects.filter(course__school__name=school_name)
            try:
                sections.get(pk=section)
            except sections.model.DoesNotExist:
                raise NotFound("Указанная секция не относится не к одному курсу этой школы.")

        instance = self.get_object()
        serializer = LessonSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("video"):
            if instance.video:
                remove_from_yandex(str(instance.video))
            base_lesson = BaseLesson.objects.get(lessons=instance)
            serializer.validated_data["video"] = upload_file(
                request.FILES["video"], base_lesson, timeout=(2000.0, 10000.0)
            )
        else:
            serializer.validated_data["video"] = instance.video

        self.perform_update(serializer)

        serializer = LessonDetailSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        base_lesson = BaseLesson.objects.get(lessons=instance)
        course = base_lesson.section.course
        school_id = course.school.school_id

        remove_resp = remove_from_yandex(
            "/{}_school/{}_course/{}_lesson".format(
                school_id, course.course_id, base_lesson.id
            )
        )
        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
