from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import SelectelClient
from courses.models import Course, Section, StudentsGroup, UserHomework
from courses.serializers import SectionSerializer
from django.db.models import Avg, OuterRef, Subquery, Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolGetSerializer, SchoolSerializer
from users.models import Profile
from users.serializers import UserProfileGetSerializer

s = SelectelClient()


class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт на получение, создания, изменения и удаления школ \n
    Разрешения для просмотра школ (любой пользователь)\n
    Разрешения для создания и изменения школы (только пользователи зарегистрированные указавшие email и phone_number')"""

    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
        else:
            return SchoolSerializer

    @action(detail=True)
    def stats(self, request, pk, *args, **kwargs):
        queryset = StudentsGroup.objects.all()
        school = self.get_object()

        first_name = self.request.GET.get("first_name")
        if first_name:
            queryset = queryset.filter(students__first_name=first_name).distinct()
        last_name = self.request.GET.get("last_name")
        if last_name:
            queryset = queryset.filter(students__last_name=last_name).distinct()
        group_name = self.request.GET.get("group_name")
        if group_name:
            queryset = queryset.filter(name=group_name).distinct()

        school_name = self.request.GET.get("school_name")
        if school_name:
            queryset = queryset.filter(school_name=school_name).distinct()
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
                    "avatar": serializer.data["avatar"],
                    "last_name": item[7],
                    "group_name": item[8],
                    "school_name": school.name,
                    "mark_sum": item[9],
                    "average_mark": item[10],
                    "sections": section_data,
                }
            )

        return Response(serialized_data)

    def get_permissions(self):

        permissions = super().get_permissions()

        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра школ (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy", "clone"]:
            # Разрешения для создания и изменения школы (только пользователи зарегистрированные')
            user = self.request.user

            if not user.is_anonymous:
                if not user.email:
                    raise PermissionDenied("Необходимо указать email.")
                elif not user.phone_number:
                    raise PermissionDenied("Необходимо указать номер телефона.")
                return permissions
            else:
                raise PermissionDenied("Необходима регистрация.")
        else:
            return permissions

    def create(self, request, *args, **kwargs):
        serializer = SchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school = serializer.save(avatar=None, owner=request.user)
        school_id = school.school_id
        if request.FILES.get("avatar"):
            avatar = s.upload_school_image(request.FILES["avatar"], school_id)
            school.avatar = avatar
            school.save()
            serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school = self.get_object()
        school_id = school.school_id

        if request.FILES.get("avatar"):
            if school.avatar:
                s.remove_from_selectel(str(school.avatar))
            school.avatar = s.upload_school_image(request.FILES["avatar"], school_id)
        school.order = request.data.get("order", school.order)
        school.name = request.data.get("name", school.name)

        school.save()
        serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Получаем список файлов, хранящихся в папке удаляемой школы
        files_to_delete = s.get_folder_files("{}_school".format(instance.pk))
        # Удаляем все файлы, связанные с удаляемой школой
        remove_resp = (
            s.bulk_remove_from_selectel(files_to_delete) if files_to_delete else None
        )

        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
