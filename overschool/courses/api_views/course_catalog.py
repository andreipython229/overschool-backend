from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import BaseLesson, Course, CourseLanding, Public
from courses.paginators import StudentsPagination
from courses.serializers import LandingGetSerializer
from courses.serializers.course_catalog import (
    CourseCatalogDetailSerializer,
    CourseCatalogSerializer,
)
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count, Q
from rest_framework import permissions, viewsets
from rest_framework.response import Response


class CourseCatalogViewSet(WithHeadersViewSet, viewsets.ReadOnlyModelViewSet):
    """
    API каталога курсов платформы
    <h2>/api/course_catalog/</h2>
    """

    serializer_class = CourseCatalogSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StudentsPagination
    http_method_names = ["get", "head", "retrieve"]

    def get_queryset(self):
        courses = Course.objects.annotate(
            baselessons_count=Count("sections__lessons")
        ).filter(baselessons_count__gte=5)
        if self.action == "retrieve":
            # Для детального просмотра курса
            return courses.filter(
                Q(is_catalog=True) | Q(is_direct=True), public=Public.PUBLISHED
            )
        else:
            # Для списка курсов в каталоге
            return courses.filter(is_catalog=True, public=Public.PUBLISHED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        # Если параметр "query" не передан, возвращаем результаты без поиска
        query = request.GET.get("query")
        if not query:
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # Создаем объект SearchQuery для запроса поиска на русском языке
        tsquery_russian = SearchQuery(query, config="russian")
        # Создаем объект SearchQuery для запроса поиска на английском языке
        tsquery_english = SearchQuery(query, config="english")
        # Создаем объект для объединения запросов поиска
        queryset_russian = queryset.annotate(
            search_russian=SearchVector("name", config="russian")
        ).filter(search_russian=tsquery_russian)

        queryset_english = queryset.annotate(
            search_english=SearchVector("name", config="english")
        ).filter(search_english=tsquery_english)

        # Объединяем результаты двух запросов
        queryset = queryset_russian | queryset_english

        # Пагинируем результаты и возвращаем полные объекты
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        course_id = self.kwargs.get("pk")
        instance = CourseLanding.objects.get(course__course_id=course_id)
        serializer = LandingGetSerializer(instance)
        return Response(serializer.data)
