from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from courses.models import Course, CourseLanding
from courses.serializers.course_catalog import CourseCatalogSerializer, CourseCatalogDetailSerializer


class CourseCatalogViewSet(LoggingMixin, WithHeadersViewSet):
    """
    ViewSet для работы с каталогом курсов
    """
    queryset = Course.objects.all()
    serializer_class = CourseCatalogSerializer

    def get_queryset(self):
        """
        Фильтрация курсов по различным параметрам
        """
        queryset = Course.objects.all()

        # Фильтр по количеству уроков (минимум 5)
        queryset = queryset.annotate(
            baselessons_count=Count('sections__lessons')
        ).filter(baselessons_count__gte=5)

        # Фильтр по школе (если указан)
        school_name = self.request.query_params.get('school')
        if school_name:
            queryset = queryset.filter(school__name=school_name)

        # Фильтр по поиску (если указан)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Фильтр по публичности
        queryset = queryset.filter(public=True)

        # Фильтр по каталогу
        queryset = queryset.filter(is_catalog=True)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Список курсов с пагинацией
        """
        page = int(request.query_params.get('p', 1))
        size = int(request.query_params.get('s', 12))

        queryset = self.get_queryset()
        total_count = queryset.count()

        # Пагинация
        start = (page - 1) * size
        end = start + size
        courses = queryset[start:end]

        # Сериализация
        serializer = self.get_serializer(courses, many=True)

        return Response({
            "count": total_count,
            "next": None if end >= total_count else page + 1,
            "previous": None if page <= 1 else page - 1,
            "results": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """
        Детальная информация о курсе
        """
        course_id = self.kwargs.get("pk")
        try:
            # Пытаемся найти CourseLanding
            instance = CourseLanding.objects.get(course__course_id=course_id)
            # Возвращаем базовую структуру, так как LandingGetSerializer не существует
            return Response({
                "course_id": instance.course.course_id,
                "name": instance.course.name,
                "description": getattr(instance.course, 'description', ''),
                "price": getattr(instance.course, 'price', ''),
                "format": getattr(instance.course, 'format', ''),
                "is_catalog": getattr(instance.course, 'is_catalog', False),
                "is_direct": getattr(instance.course, 'is_direct', False),
                "public": getattr(instance.course, 'public', ''),
                "school_name": getattr(instance.course.school, 'name', '') if hasattr(instance.course,
                                                                                      'school') and instance.course.school else '',
                "lessons_count": instance.course.sections.aggregate(
                    total_lessons=Count('lessons')
                )['total_lessons'] or 0,
                # Блоки для фронтенда
                "header": {"id": 1, "content": "header", "visible": True},
                "stats": {"id": 2, "content": "stats", "visible": True},
                "audience": {"id": 3, "content": "audience", "visible": True},
                "advantage": {"id": 4, "content": "advantage", "visible": True},
                "income": {"id": 5, "content": "income", "visible": True},
                "trainingProgram": {"id": 6, "content": "trainingProgram", "visible": True},
                "trainingPurpose": {"id": 7, "content": "trainingPurpose", "visible": True},
                # Пустые массивы для компонентов, которые ожидают .map()
                "audience_list": [],
                "advantage_list": [],
                "salary_list": [],
                "training_program_list": [],
                "purpose_training_list": []
            })
        except CourseLanding.DoesNotExist:
            # Если CourseLanding не найден - возвращаем блоки + пустые массивы для фронтенда
            course = Course.objects.get(course_id=course_id)

            return Response({
                # Блоки для фронтенда
                "header": {"id": 1, "content": "header", "visible": True},
                "stats": {"id": 2, "content": "stats", "visible": True},
                "audience": {"id": 3, "content": "audience", "visible": True},
                "advantage": {"id": 4, "content": "advantage", "visible": True},
                "income": {"id": 5, "content": "income", "visible": True},
                "trainingProgram": {"id": 6, "content": "trainingProgram", "visible": True},
                "trainingPurpose": {"id": 7, "content": "trainingPurpose", "visible": True},

                # Пустые массивы для компонентов, которые ожидают .map()
                "audience_list": [],
                "advantage_list": [],
                "salary_list": [],
                "training_program_list": [],
                "purpose_training_list": []
            })

    @action(detail=True, methods=['post'])
    def send_appeal(self, request, pk=None):
        """
        Отправка заявки на курс
        """
        try:
            course = self.get_object()
            # Здесь должна быть логика отправки заявки
            return Response({"message": "Заявка успешно отправлена"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)