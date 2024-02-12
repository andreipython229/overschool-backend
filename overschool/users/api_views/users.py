from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import BaseLesson, StudentsGroup, UserProgressLogs
from courses.paginators import StudentsPagination
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import School
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import AllUsersSerializer, UserSerializer


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Возвращаем только объекты пользователя, сделавшего запрос\n
    <h2>/api/user/</h2>\n
    Возвращаем только объекты пользователя, сделавшего запрос"""

    serializer_class = UserSerializer
    permission_classes = [OwnerUserPermissions]
    http_method_names = ["get", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        return User.objects.filter(id=self.request.user.id)


class AllUsersViewSet(viewsets.GenericViewSet):
    """Возвращаем всех пользователей\n
    <h2>/api/user/</h2>\n
    Возвращаем всех пользователей"""

    queryset = User.objects.all()
    serializer_class = AllUsersSerializer
    pagination_class = StudentsPagination

    def list(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")

        # Найти объект школы по имени
        try:
            school = School.objects.get(name=school_name)
        except School.DoesNotExist:
            return Response(
                {"error": "School not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Проверить, является ли текущий пользователь администратором указанной школы
        user = request.user
        is_admin = user.groups.filter(group__name="Admin", school=school).exists()

        # Получаем параметры запроса
        role = request.GET.get("role")

        if is_admin:
            # Если пользователь - админ, вернуть только пользователей из этой школы
            if role == "student":
                queryset = User.objects.filter(
                    groups__school=school, groups__group__name="Student"
                ).distinct()
            elif role == "staff":
                queryset = (
                    User.objects.filter(groups__school=school)
                    .exclude(groups__group__name="Student")
                    .distinct()
                )
            else:
                queryset = User.objects.filter(groups__school=school).distinct()
            # Применяем пагинацию к queryset
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(
                    page, many=True, context={"school": school}
                )
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(
                queryset, many=True, context={"school": school}
            )
            return Response(serializer.data)
        else:
            # В противном случае вернуть ошибку доступа
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )


class GetCertificateView(APIView):
    serializer_class = None
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = self.request.data.get("user_id")
        course_id = self.request.data.get("course_id")
        school_id = self.request.data.get("school_id")

        groups = StudentsGroup.objects.filter(
            students=user_id, course_id=course_id, certificate=True
        )

        if not groups.exists():
            return Response(
                {"error": "У вас нет доступа к сертификату"},
                status=status.HTTP_403_FORBIDDEN,
            )

        group = groups.first()
        course = group.course_id
        base_lessons = BaseLesson.objects.filter(section__course=course, active=True)

        for base_lesson in base_lessons:
            try:
                progress = UserProgressLogs.objects.get(
                    user=user_id, lesson=base_lesson
                )
                if not progress.completed:
                    return Response(
                        {"error": f"Необходимо пройти урок {base_lesson.name}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except UserProgressLogs.DoesNotExist:
                return Response(
                    {"error": f"Необходимо пройти урок {base_lesson.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        school = get_object_or_404(School, school_id=school_id)
        user = get_object_or_404(User, id=user_id)
        owner = get_object_or_404(User, id=school.owner.id)
        teacher = get_object_or_404(User, id=group.teacher_id.id)

        certificate_data = {
            "school_name": school.name,
            "school_owner": f"{owner.last_name} {owner.first_name} {owner.patronymic}",
            "teacher": f"{teacher.last_name} {teacher.first_name} {teacher.patronymic}",
            "user_full_name": f"{user.last_name} {user.first_name} {user.patronymic}",
            "course_name": course.name,
            "course_description": course.description,
        }

        return Response(certificate_data, status=status.HTTP_200_OK)
