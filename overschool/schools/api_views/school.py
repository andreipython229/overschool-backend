from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.models import Course, Section, StudentsGroup, UserHomework, LessonAvailability
from courses.models.students.students_history import StudentsHistory
from courses.serializers import SectionSerializer
from django.db.models import Avg, Sum
from django.db.models import Subquery, OuterRef
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School, SchoolHeader, Tariff, TariffPlan
from schools.serializers import (
    SchoolGetSerializer,
    SchoolSerializer,
    SchoolUpdateSerializer,
    SelectTrialSerializer,
    TariffSerializer,
)
from users.models import Profile, UserGroup, UserRole
from users.serializers import UserProfileGetSerializer
from courses.services import get_student_progress
from .schemas.school import SchoolsSchemas

s3 = UploadToS3()


@method_decorator(
    name="partial_update",
    decorator=SchoolsSchemas.partial_update_schema(),
)
class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления школ \n
    <h2>/api/{school_name}/schools/</h2>\n
    Разрешения для просмотра школ (любой пользователь)\n
    Разрешения для создания и изменения школы (только пользователи зарегистрированные указавшие email и phone_number')"""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
        if self.action in ["select_trial"]:
            return SelectTrialSerializer
        else:
            return SchoolSerializer

    def get_permissions(self):

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin").exists():
            return permissions
        if user.is_authenticated and self.action in ["create"]:
            return permissions
        if (
                self.action in ["stats"]
                and user.groups.filter(group__name__in=["Teacher", "Admin"]).exists()
        ):
            return permissions
        if self.action in ["list", "retrieve", "create"]:
            # Разрешения для просмотра домашних заданий (любой пользователь школы)
            if user.groups.filter(group__name__in=["Teacher", "Student"]).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                School.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        queryset = School.objects.filter(groups__user=user).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        if not request.user.email or not request.user.phone_number:
            raise PermissionDenied("Email и phone number пользователя обязательны.")
        # Проверка количества школ, которыми владеет пользователь
        if School.objects.filter(owner=request.user).count() >= 2:
            raise PermissionDenied(
                "Пользователь может быть владельцем только двух школ."
            )

        serializer = SchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if School.objects.filter(name=serializer.validated_data["name"]).exists():
            return HttpResponse("Название школы уже существует.", status=400)

        school = serializer.save(
            owner=request.user,
            tariff=Tariff.objects.get(name=TariffPlan.INTERN.value),
        )
        if school:
            SchoolHeader.objects.create(school=school, name=school.name)
        # Создание записи в модели UserGroup для добавления пользователя в качестве администратора
        group_admin = UserRole.objects.get(name="Admin")
        user_group = UserGroup(user=request.user, group=group_admin, school=school)
        user_group.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school = self.get_object()
        user = self.request.user
        if not user.groups.filter(group__name="Admin", school=school).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        serializer = SchoolUpdateSerializer(school, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        name_data = serializer.validated_data.get("name")
        if name_data:
            existing_school = (
                School.objects.filter(name=name_data).exclude(pk=school.pk).first()
            )
            if existing_school:
                return Response(
                    "Название школы уже существует.", status=status.HTTP_400_BAD_REQUEST
                )

        self.perform_update(serializer)
        serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            raise PermissionDenied("У вас нет разрешения на удаление этой школы.")

        # Получаем список файлов, хранящихся в папке удаляемой школы
        files_to_delete = s3.get_list_objects("{}_school".format(instance.pk))
        # Удаляем все файлы и сегменты, связанные с удаляемой школой
        remove_resp = None
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

    @action(detail=True, methods=["post"])
    def select_trial(self, request, pk=None):
        school = self.get_object()

        # Проверка разрешений для выбора пробного тарифа
        if school.owner != request.user:
            return Response(
                {
                    "error": "У вас нет прав на установку пробного периода для этой школы"
                },
                status=403,
            )

        # Проверка, что пробный тариф еще не использован
        if not school.used_trial:
            serializer = SelectTrialSerializer(school, data=request.data)
            serializer.is_valid(raise_exception=True)
            tariff_choice = serializer.validated_data["tariff"]

            # Получение объекта Tariff по выбранному тарифу
            try:
                tariff = Tariff.objects.get(name=tariff_choice)
            except Tariff.DoesNotExist:
                return Response({"error": "Указан некорректный тариф"}, status=400)
            # Установка выбранного тарифа для школы
            school.tariff = tariff
            school.used_trial = True
            school.trial_end_date = timezone.now() + timezone.timedelta(days=14)
            school.save()

            return Response(
                {"message": "Пробный период успешно установлен"}, status=200
            )
        else:
            return Response({"error": "Пробный период уже был использован"}, status=400)

    @action(detail=True)
    def stats(self, request, pk, *args, **kwargs):
        queryset = StudentsGroup.objects.none()
        user = self.request.user
        school = self.get_object()
        if user.groups.filter(group__name="Teacher", school=school).exists():
            queryset = StudentsGroup.objects.filter(
                teacher_id=request.user, course_id__school=school
            )
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = StudentsGroup.objects.filter(course_id__school=school)
        all_active_students = queryset.count()
        deleted_history_queryset = StudentsHistory.objects.none()
        show_deleted = self.request.GET.get("show_deleted")

        if not show_deleted:
            deleted_history_queryset = StudentsHistory.objects.filter(students_group_id__course_id__school=school,
                                                                      is_deleted=True)

        # Фильтры
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(user__first_name=first_name).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(user__last_name=last_name).distinct()
        course_name = self.request.GET.get("course_name")
        if course_name:
            queryset = queryset.filter(course_id__name=course_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__course_id__name=course_name).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                students_group_id__name=group_name).distinct()
        last_active_min = self.request.GET.get("last_active_min")
        if last_active_min:
            queryset = queryset.filter(
                students__date_joined__gte=last_active_min
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__date_joined__gte=last_active_min).distinct()
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_max:
            queryset = queryset.filter(
                students__date_joined__lte=last_active_max
            ).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__date_joined__lte=last_active_max).distinct()
        last_active = self.request.GET.get("last_active")
        if last_active:
            queryset = queryset.filter(students__date_joined=last_active).distinct()
            deleted_history_queryset = deleted_history_queryset.filter(
                user__date_joined=last_active).distinct()
        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__exact=mark_sum)
            deleted_history_queryset = deleted_history_queryset.annotate(mark_sum=Sum("user__user_homeworks__mark"))
            deleted_history_queryset = deleted_history_queryset.filter(mark_sum__exact=mark_sum)

        average_mark = self.request.GET.get("average_mark")
        if average_mark:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__exact=average_mark)
            deleted_history_queryset = deleted_history_queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            deleted_history_queryset = deleted_history_queryset.filter(average_mark__exact=average_mark)
        mark_sum_min = self.request.GET.get("mark_sum_min")
        if mark_sum_min:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__gte=mark_sum_min)
        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_max:
            queryset = queryset.annotate(mark_sum=Sum("students__user_homeworks__mark"))
            queryset = queryset.filter(mark_sum__lte=mark_sum_max)
        average_mark_min = self.request.GET.get("average_mark_min")
        if average_mark_min:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__gte=average_mark_min)
        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_max:
            queryset = queryset.annotate(
                average_mark=Avg("students__user_homeworks__mark")
            )
            queryset = queryset.filter(average_mark__lte=average_mark_max)

        subquery_mark_sum = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
                .values("user_id")
                .annotate(mark_sum=Sum("mark"))
                .values("mark_sum")
        )

        subquery_average_mark = (
            UserHomework.objects.filter(user_id=OuterRef("students__id"))
                .values("user_id")
                .annotate(avg=Avg("mark"))
                .values("avg")
        )

        subquery_date_added = (
            StudentsHistory.objects.filter(
                user_id=OuterRef("students__id"),
                students_group=OuterRef("group_id"),
                is_deleted=False
            )
                .order_by("-date_added")
                .values("date_added")
        )

        subquery_date_removed = (
            StudentsHistory.objects.none(
            )
                .order_by("-date_removed")
                .values("date_removed")
        )

        data = queryset.values(
            "course_id",
            "course_id__name",
            "group_id",
            "students__date_joined",
            "students__email",
            "students__first_name",
            "students__id",
            "students__profile__avatar",
            "students__last_name",
            "name",
        ).annotate(
            mark_sum=Subquery(subquery_mark_sum),
            average_mark=Subquery(subquery_average_mark),
            date_added=Subquery(subquery_date_added),
            date_removed=Subquery(subquery_date_removed),
        )
        lesson_availability_data = LessonAvailability.objects.filter(student_id=OuterRef("students__id")).values(
            "available")
        data = data.annotate(available=Subquery(lesson_availability_data[:1]))

        filtered_active_students = queryset.count()

        serialized_data = []
        for item in data:
            if not item["students__id"]:
                continue
            profile = Profile.objects.filter(user_id=item["students__id"]).first()
            if profile is not None:
                serializer = UserProfileGetSerializer(
                    profile, context={"request": self.request}
                )
            courses = Course.objects.filter(course_id=item["course_id"])
            sections = Section.objects.filter(course__in=courses)
            section_data = SectionSerializer(sections, many=True).data
            serialized_data.append(
                {
                    "course_id": item["course_id"],
                    "course_name": item["course_id__name"],
                    "group_id": item["group_id"],
                    "last_active": item["students__date_joined"],
                    "email": item["students__email"],
                    "first_name": item["students__first_name"],
                    "student_id": item["students__id"],
                    "avatar": serializer.data["avatar"],
                    "last_name": item["students__last_name"],
                    "group_name": item["name"],
                    "school_name": school.name,
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "sections": section_data,
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "is_deleted": False,
                    "available": item["available"],
                    "progress": get_student_progress(item['students__id'], item["course_id"]),
                    "all_active_students": all_active_students,
                    "filtered_active_students": filtered_active_students,
                }
            )

        # Deleted students
        subquery_mark_sum_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
                .values("user_id")
                .annotate(mark_sum=Sum("mark"))
                .values("mark_sum")
        )

        subquery_average_mark_deleted = (
            UserHomework.objects.filter(user_id=OuterRef("user_id"))
                .values("user_id")
                .annotate(avg=Avg("mark"))
                .values("avg")
        )

        data_deleted = deleted_history_queryset.values(
            "students_group_id__course_id",
            "students_group_id__course_id__name",
            "students_group_id",
            "user_id__date_joined",
            "user_id__email",
            "user_id__first_name",
            "user_id",
            "user_id__profile__avatar",
            "user_id__last_name",
            "students_group_id__name",
            "date_added",
            "date_removed"
        ).annotate(
            mark_sum=Subquery(subquery_mark_sum_deleted),
            average_mark=Subquery(subquery_average_mark_deleted),
        )

        for item in data_deleted:
            if not item["user_id"]:
                continue
            profile = Profile.objects.filter(user_id=item["user_id"]).first()
            if profile is not None:
                serializer = UserProfileGetSerializer(
                    profile, context={"request": self.request}
                )
            courses = Course.objects.filter(course_id=item["students_group_id__course_id"])
            sections = Section.objects.filter(course__in=courses)
            section_data = SectionSerializer(sections, many=True).data
            serialized_data.append(
                {
                    "course_id": item["students_group_id__course_id"],
                    "course_name": item["students_group_id__course_id__name"],
                    "group_id": item["students_group_id"],
                    "last_active": item["user_id__date_joined"],
                    "email": item["user_id__email"],
                    "first_name": item["user_id__first_name"],
                    "student_id": item["user_id"],
                    "avatar": serializer.data["avatar"],
                    "last_name": item["user_id__last_name"],
                    "group_name": item["students_group_id__name"],
                    "school_name": school.name,
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "sections": section_data,
                    "date_added": item["date_added"],
                    "date_removed": item["date_removed"],
                    "is_deleted": True,
                }
            )

        return Response(serialized_data)


SchoolViewSet = apply_swagger_auto_schema(
    tags=["schools"], excluded_methods=["partial_update"]
)(SchoolViewSet)


class TariffViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    API endpoint для тарифов.

    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    http_method_names = ["get", "head"]
