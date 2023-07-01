from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_school_image
from courses.models import Course, Section, StudentsGroup, UserHomework
from courses.serializers import SectionSerializer
from django.db.models import Avg, OuterRef, Subquery, Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolGetSerializer, SchoolSerializer
from users.models import Profile, UserGroup, UserRole
from users.serializers import UserProfileGetSerializer


class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления школ \n
    Разрешения для просмотра школ (любой пользователь)\n
    Разрешения для создания и изменения школы (только пользователи зарегистрированные указавшие email и phone_number')"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
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
        user = self.request.user
        queryset = School.objects.filter(groups__user=user)
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
        school = serializer.save(avatar=None, owner=request.user)
        # Создание записи в модели UserGroup для добавления пользователя в качестве администратора
        group_admin = UserRole.objects.get(name="Admin")
        user_group = UserGroup(user=request.user, group=group_admin, school=school)
        user_group.save()

        school_id = school.school_id
        if request.FILES.get("avatar"):
            avatar = upload_school_image(request.FILES["avatar"], school_id)
            school.avatar = avatar
            school.save()
            serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school = self.get_object()
        user = self.request.user
        if not user.groups.filter(group__name="Admin", school=school).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        school_id = school.school_id

        if request.FILES.get("avatar"):
            if school.avatar:
                remove_from_yandex(str(school.avatar))
            school.avatar = upload_school_image(request.FILES["avatar"], school_id)
        school.order = request.data.get("order", school.order)
        school.name = request.data.get("name", school.name)

        school.save()
        serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            raise PermissionDenied("У вас нет разрешения на удаление этой школы.")
        remove_resp = remove_from_yandex("/{}_school".format(instance.school_id))
        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()

        last_active_min = self.request.GET.get("last_active_min")
        last_active_max = self.request.GET.get("last_active_max")
        if last_active_min and last_active_max:
            queryset = queryset.filter(
                students__date_joined__range=[last_active_min, last_active_max]
            ).distinct()

        mark_sum_min = self.request.GET.get("mark_sum_min")
        mark_sum_max = self.request.GET.get("mark_sum_max")
        if mark_sum_min and mark_sum_max:
            queryset = queryset.filter(
                students__user_homeworks__mark__range=[mark_sum_min, mark_sum_max]
            ).distinct()

        average_mark_min = self.request.GET.get("average_mark_min")
        average_mark_max = self.request.GET.get("average_mark_max")
        if average_mark_min and average_mark_max:
            queryset = queryset.filter(
                students__user_homeworks__average_mark__range=[
                    average_mark_min,
                    average_mark_max,
                ]
            ).distinct()

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

        data = queryset.values_list(
            "course_id",
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
        )

        serialized_data = []
        for item in data:
            profile = Profile.objects.get(user_id=item[5])
            serializer = UserProfileGetSerializer(profile)
            courses = Course.objects.filter(school=school)
            sections = Section.objects.filter(course__in=courses)
            section_data = SectionSerializer(sections, many=True).data
            serialized_data.append(
                {
                    "course_id": item[0],
                    "group_id": item[1],
                    "last_active": item[2],
                    "email": item[3],
                    "first_name": item[4],
                    "student_id": item[5],
                    "avatar": serializer.data["avatar_url"],
                    "last_name": item[7],
                    "group_name": item[8],
                    "school_name": school.name,
                    "mark_sum": item[9],
                    "average_mark": item[10],
                    "sections": section_data,
                }
            )

        return Response(serialized_data)
