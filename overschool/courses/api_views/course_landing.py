import json
from datetime import datetime, timedelta

import pytz
from chats.models import Chat, UserChat
from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from courses.api_views.students_group import get_student_training_duration
from courses.models import (
    Course,
    HeaderBlock,
    StatsBlock,
    BlockCards,
    AudienceBlock,
    TrainingProgram,
    TrainingPurpose,
    CourseLanding,
    Folder,
    Homework,
    Lesson,
    SectionTest,
    StudentsGroup,
    TrainingDuration,
    UserProgressLogs,
    UserTest,
)
from courses.models.courses.course import Public
from courses.models.courses.section import Section
from courses.models.homework.user_homework import UserHomework
from courses.models.students.students_history import StudentsHistory
from courses.paginators import StudentsPagination, UserHomeworkPagination
from courses.serializers import (
    LandingGetSerializer,
    CourseInfoSerializer,
    HeaderLandingSerializer,
    StatsGetSerializer,
    BlockCardsSerializer,
    BlockCardsPhotoSerializer,
    BlockCardsGetSerializer,
    AudienceSerializer,
    TrainingProgramSerializer,
    TrainingPurposeSerializer,
)
from courses.services import get_student_progress, progress_subquery
from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import ExtractDay, Now
from django.db.models.lookups import GreaterThan, LessThan
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import Profile
from users.serializers import UserProfileGetSerializer
from .utils import convert_landing_data

from .schemas.course import CoursesSchemas

s3 = UploadToS3()


# @method_decorator(
#     name="update",
#     decorator=CoursesSchemas.courses_update_schema(),
# )
# @method_decorator(
#     name="partial_update",
#     decorator=CoursesSchemas.courses_update_schema(),
# )
class CourseLandingViewSet(LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """Эндпоинт для просмотра, создания, изменения и удаления курсов \n
    <h2>/api/{school_name}/courses_landing/</h2>\n
    Получать лендинг курса может любой пользователь. \n
    Создавать, изменять, удалять - пользователь с правами группы Admin."""

    serializer_class = LandingGetSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "retrieve", "update", "patch"]
    # parser_classes = (MultiPartParser,)

    # def get_permissions(self, *args, **kwargs):
    #     return permissions
    #
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                CourseLanding.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы

        return CourseLanding.objects.all()

    def get_serializer_class(self):
        # if self.action == "retrieve":
        #     return LandingGetSerializer
        return LandingGetSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        course_id = self.kwargs.get("pk")
        instance = CourseLanding.objects.get(course__course_id=course_id)

        # обработка и разброс данных по моделям
        def initUpdate(data_dict):
            converted_data = convert_landing_data(data_dict)
            header_serializer = HeaderLandingSerializer(instance.header,
                                                        data=converted_data["header"],
                                                        partial=partial)
            course_serializer = CourseInfoSerializer(instance.course,
                                                     data=converted_data["course"],
                                                     partial=partial)
            audience_serializer = AudienceSerializer(instance.audience,
                                                     data=converted_data["audience"],
                                                     partial=partial)
            training_program_serializer = TrainingProgramSerializer(instance.training_program,
                                                                    data=converted_data["training_program"],
                                                                    partial=partial)
            training_purpose_serializer = TrainingPurposeSerializer(instance.training_purpose,
                                                                    data=converted_data["training_purpose"],
                                                                    partial=partial)
            header_serializer.is_valid(raise_exception=True)
            course_serializer.is_valid(raise_exception=True)
            audience_serializer.is_valid(raise_exception=True)
            training_program_serializer.is_valid(raise_exception=True)
            training_purpose_serializer.is_valid(raise_exception=True)

            self.perform_update(header_serializer)
            self.perform_update(course_serializer)
            self.perform_update(audience_serializer)
            self.perform_update(training_program_serializer)
            self.perform_update(training_purpose_serializer)

        # случай, когда данные летаят с файлами через formdata
        if "formdata" in request.data:
            data_dict = json.loads(request.data["formdata"])
            initUpdate(data_dict)


        # случай, когда данны летят словарём
        if "header" in request.data:
            initUpdate(request.data)

        # если есть какие-либо фото-файлы
        photo_keys = [key for key in request.FILES.keys() if key.startswith('photo')]
        if photo_keys:
            # если есть изображение бэкраунда курса
            if "photo_background" in request.FILES:
                course_serializer = CourseInfoSerializer(instance.course, data={}, partial=partial)
                course_serializer.is_valid(raise_exception=True)
                if instance.course.photo:
                    s3.delete_file(str(instance.course.photo))
                course_serializer.validated_data["photo"] = s3.upload_course_image(
                    request.FILES["photo_background"], instance.course
                )
                self.perform_update(course_serializer)

            # если есть изображения карточек блока "Целевая аудитория"
            photo_audience_keys = [key for key in photo_keys if key.startswith('photo_audience_')]
            if photo_audience_keys:
                for key in photo_audience_keys:
                    # Извлекаем число из ключа
                    position = int(key.split('_')[-1])
                    chip = instance.audience.chips.get(position=position)
                    block_card_serializer = BlockCardsPhotoSerializer(chip, data={}, partial=partial)
                    block_card_serializer.is_valid(raise_exception=True)
                    if chip.photo:
                        s3.delete_file(str(chip.photo))
                    block_card_serializer.validated_data["photo"] = s3.upload_course_landing_images(
                        request.FILES[key], instance.course
                    )
                    self.perform_update(block_card_serializer)

        # формируем обновлённую пачку данных по лендингу для возврата
        inst = CourseLanding.objects.get(course__course_id=course_id)
        srlzr = LandingGetSerializer(inst)

        return Response(srlzr.data)

    def retrieve(self, request, *args, **kwargs):
        course_id = self.kwargs.get("pk")
        try:
            instance = CourseLanding.objects.get(course__course_id=course_id)
            serializer = LandingGetSerializer(instance)
            return Response(serializer.data)
        except:
            # создаём новый лендинг, если до этого не был создан
            course = Course.objects.get(course_id=course_id)
            header = HeaderBlock.objects.create(
                is_visible=True,
                position=0,
                can_up=False,
                can_down=False,
            )
            stats = StatsBlock.objects.create(
                is_visible=True,
                position=1,
                can_up=False,
                can_down=False,
            )
            aud_chip_1 = BlockCards.objects.create(
                position=0,
                title="Карточка 1",
                description="",
            )
            aud_chip_2 = BlockCards.objects.create(
                position=1,
                title="Карточка 2",
                description="",
            )
            audience = AudienceBlock.objects.create(
                is_visible=True,
                position=2,
                can_up=False,
                can_down=True,
                description="",
            )
            audience.chips.set([aud_chip_1, aud_chip_2]),
            training_program = TrainingProgram.objects.create(
                is_visible=True,
                position=3,
                can_up=True,
                can_down=True,
            )
            purp_chip_1 = BlockCards.objects.create(
                position=0,
                title="Навык 1",
                description="",
            )
            purp_chip_2 = BlockCards.objects.create(
                position=1,
                title="Навык 2",
                description="",
            )
            training_purpose = TrainingPurpose.objects.create(
                is_visible=True,
                position=4,
                can_up=True,
                can_down=False,
                description="",
            )
            training_purpose.chips.set([purp_chip_1, purp_chip_2])
            landing = CourseLanding.objects.create(
                course=course,
                header=header,
                stats=stats,
                audience=audience,
                training_program=training_program,
                training_purpose=training_purpose,
            )
            serializer = LandingGetSerializer(landing)
            return Response(serializer.data)
