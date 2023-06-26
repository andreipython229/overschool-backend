from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_school_image
from courses.models import StudentsGroup, UserHomework, Course, Section
from courses.serializers import SectionSerializer
from django.db.models import Sum, Avg, Subquery, OuterRef
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.serializers import SchoolGetSerializer, SchoolSerializer
from users.models import Profile
from users.serializers import UserProfileGetSerializer


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
        last_active = self.request.GET.get("last_active")
        if last_active:
            queryset = queryset.filter(students__date_joined=last_active).distinct()

        mark_sum = self.request.GET.get("mark_sum")
        if mark_sum:
            queryset = queryset.filter(students__user_homeworks__mark__gte=mark_sum).distinct()

        subquery_mark_sum = UserHomework.objects.filter(user_id=OuterRef("students__id")).values("user_id").annotate(
            mark_sum=Sum("mark")
        ).values("mark_sum")

        subquery_average_mark = UserHomework.objects.filter(user_id=OuterRef("students__id")).values(
            "user_id").annotate(avg=Avg("mark")).values("avg")

        data = queryset.values_list(
            'course_id',
            'group_id',
            'students__date_joined',
            'students__email',
            'students__first_name',
            'students__id',
            'students__profile__avatar',
            'students__last_name',

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
                    "mark_sum": item[8],
                    "average_mark": item[9],
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
            avatar = upload_school_image(request.FILES["avatar"], school_id)
            school.avatar = avatar
            school.save()
            serializer = SchoolGetSerializer(school)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        school = self.get_object()
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
        remove_resp = remove_from_yandex("/{}_school".format(instance.school_id))
        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
