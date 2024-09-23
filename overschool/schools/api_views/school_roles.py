from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from users.models.user import User
from schools.models import SchoolNewRole, School
from schools.serializers import SchoolNewRoleSerializer


class SchoolNewRoleViewSet(viewsets.ViewSet):
    """
    API ендпоинт для управления дополнительными ролями пользователей
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def assign_role(self, request):
        school_id = request.data.get("school_id")
        user_id = request.data.get("user_id")
        role_name = request.data.get("role_name")

        try:
            school = School.objects.get(school_id=school_id)
            user = User.objects.get(id=user_id)

            # Проверяем, есть ли уже такая роль у пользователя в данной школе
            if SchoolNewRole.objects.filter(school=school, user=user, role_name=role_name).exists():
                return Response({"error": {"type": "role_exists",
                                           "message": "Роль уже назначена этому пользователю в данной школе."}},
                                status=status.HTTP_400_BAD_REQUEST)

            # Если роли нет, создаем роль
            SchoolNewRole.objects.create(school=school, user=user, role_name=role_name)
            return Response({"detail": "Роль выдана успешно!"}, status=status.HTTP_201_CREATED)

        except School.DoesNotExist:
            return Response({"error": {"type": "school_not_found", "message": "Школа не найдена."}},
                            status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": {"type": "user_not_found", "message": "Пользователь не найден."}},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": {"type": "unknown_error", "message": str(e)}}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def remove_role(self, request):
        school_id = request.data.get("school_id")
        user_id = request.data.get("user_id")
        role_name = request.data.get("role_name")

        try:
            role = SchoolNewRole.objects.get(school_id=school_id, user_id=user_id, role_name=role_name)
            role.delete()
            return Response({"detail": "Role removed successfully."}, status=status.HTTP_204_NO_CONTENT)
        except SchoolNewRole.DoesNotExist:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_roles_by_user(self, request, user_id=None):
        user_id = request.query_params.get("user_id")

        try:
            roles = SchoolNewRole.objects.filter(user_id=user_id)
            serializer = SchoolNewRoleSerializer(roles, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
