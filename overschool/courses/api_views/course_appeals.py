from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import CourseAppeals
from courses.paginators import StudentsPagination
from courses.serializers.course_appeals import CourseAppealsSerializer
from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin

User = get_user_model()


class GetAppealsViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.GenericViewSet
):
    """
    Эндпоинт просмотра обращений
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseAppealsSerializer
    pagination_class = StudentsPagination
    http_method_names = ["get", "head", "retrieve"]

    def get_queryset(self):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(group__name="Admin", school=school).exists():
            queryset = CourseAppeals.objects.filter(course__school=school)
        else:
            queryset = CourseAppeals.objects.none()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Обновляем поле is_read при доступе к сообщению
        if not instance.is_read:
            instance.is_read = True
            instance.save()

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class CourseAppealsViewSet(LoggingMixin, WithHeadersViewSet, viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = CourseAppealsSerializer
    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
