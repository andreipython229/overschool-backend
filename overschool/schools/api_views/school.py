from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_school_image
from courses.models import StudentsGroup, UserTest
from django.db.models import Avg, Count, F, Sum
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
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SchoolGetSerializer
        else:
            return SchoolSerializer

    @action(detail=True)
    def stats(self, request, pk, *args, **kwargs):
        """Статистика учеников школы\n
        Статистика учеников школы"""
        queryset = StudentsGroup.objects.all()
        data = queryset.values(
            course=F("course_id"),
            email=F("students__email"),
            student_name=F("students__first_name"),
            student=F("students__id"),
            avatar=F("students__profile__avatar"),
            group=F("group_id"),
            last_active=F("students__date_joined"),
            update_date=F("students__date_joined"),
            ending_date=F("students__date_joined"),
        ).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100)
            / Count("course_id__sections__lessons"),
        )

        serialized_data = []
        for item in data:
            profile = Profile.objects.get(user_id=item["student"])
            serializer = UserProfileGetSerializer(profile)
            serialized_data.append(
                {
                    "course": item["course"],
                    "email": item["email"],
                    "student_name": item["student_name"],
                    "student": item["student"],
                    "avatar": serializer.data["avatar_url"],
                    "group": item["group"],
                    "last_active": item["last_active"],
                    "update_date": item["update_date"],
                    "ending_date": item["ending_date"],
                    "mark_sum": item["mark_sum"],
                    "average_mark": item["average_mark"],
                    "progress": item["progress"],
                }
            )
        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                .values("user")
                .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += mark_sum // 10 if bool(mark_sum) else 0
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

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
