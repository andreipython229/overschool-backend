from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import BaseLesson, StudentsGroup, UserProgressLogs
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

        if is_admin:
            # Если пользователь - админ, вернуть только пользователей из этой школы
            queryset = User.objects.filter(groups__school=school).distinct()
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

        groups = StudentsGroup.objects.filter(students=user_id, course_id=course_id, certificate=True)

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
                progress = UserProgressLogs.objects.get(user=user_id, lesson=base_lesson)
                if not progress.completed:
                    return Response(
                        {"error": f"Необходимо пройти урок {base_lesson.name}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except UserProgressLogs.DoesNotExist:
                return Response(
                    {"error": f"Необходимо пройти урок {base_lesson.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        user = get_object_or_404(User, id=user_id)
        certificate_data = {
            "user_full_name": f"{user.last_name} {user.first_name} {user.patronymic}",
            "course_name": course.name,
            "course_description": course.description,
            "lessons": [],
        }

        for base_lesson in base_lessons:
            lesson_data = {
                "lesson_name": base_lesson.name,
            }
            certificate_data["lessons"].append(lesson_data)

        return Response(certificate_data, status=status.HTTP_200_OK)
