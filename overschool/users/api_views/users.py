from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from schools.models import School
from users.models import User
from courses.models import Course, BaseLesson, UserProgressLogs
from users.permissions import OwnerUserPermissions
from users.serializers import AllUsersSerializer, UserSerializer
from rest_framework.decorators import action
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


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

    @action(detail=False, methods=['GET'])
    @action(detail=False, methods=['GET'])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('course_id', openapi.IN_QUERY, description='ID курса', type=openapi.TYPE_INTEGER),
        ],
    )
    @action(detail=False, methods=['GET'])
    def generate_certificate(self, request):
        user = self.request.user

        try:
            course_id = request.query_params.get('course_id')
            course = Course.objects.get(course_id=course_id)  # Изменено здесь
        except Course.DoesNotExist:
            return Response({"error": "Курс не найден"}, status=status.HTTP_404_NOT_FOUND)

        base_lessons = BaseLesson.objects.filter(section__course=course)
        for base_lesson in base_lessons:
            try:
                progress = UserProgressLogs.objects.get(user=user, lesson=base_lesson)
                if not progress.completed:
                    return Response({"error": f"Необходимо пройти урок {base_lesson.name}."},
                                    status=status.HTTP_400_BAD_REQUEST)
            except UserProgressLogs.DoesNotExist:
                return Response({"error": f"Необходимо пройти урок {base_lesson.name}."},
                                status=status.HTTP_400_BAD_REQUEST)

        certificate_data = {
            "user_full_name": f"{user.last_name} {user.first_name} {user.patronymic}",
            "course_name": course.name,
        }

        for base_lesson in base_lessons:
            lesson_data = {
                "lesson_name": base_lesson.name,
                "description": base_lesson.description,
            }
            certificate_data["lessons"].append(lesson_data)

        return Response(certificate_data, status=status.HTTP_200_OK)


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
            queryset = User.objects.filter(groups__school=school)
            serializer = self.get_serializer(
                queryset, many=True, context={"school": school}
            )
            return Response(serializer.data)
        else:
            # В противном случае вернуть ошибку доступа
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )