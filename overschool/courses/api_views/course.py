from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_course_image
from courses.models import (
    Course,
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
    UserProgressLogs,
    UserTest,
    UserProgressLogs
)
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    CourseGetSerializer,
    CourseSerializer,
    CourseStudentsSerializer,
    StudentsGroupSerializer,
    UserHomeworkSerializer,
)
from django.db.models import Avg, Count, F, Sum
from django.forms.models import model_to_dict
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

class CourseViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    ''' Эндпоинт для просмотра, создания, изменения и удаления курсов \n
        Получать курсы может любой пользователь. \n
        Создавать, изменять, удалять - пользователь с правами группы Admin.'''
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CourseGetSerializer
        else:
            return CourseSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра курсов (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy", "clone"]:
            # Разрешения для создания и изменения курсов (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions


    def create(self, request, *args, **kwargs):
        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save(photo=None)

        if request.FILES.get("photo"):
            photo = upload_course_image(request.FILES["photo"], course)
            course.photo = photo
            course.save()
            serializer = CourseGetSerializer(course)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("photo"):
            if instance.photo:
                remove_from_yandex(str(instance.photo))
            serializer.validated_data["photo"] = upload_course_image(
                request.FILES["photo"], instance
            )
        else:
            serializer.validated_data["photo"] = instance.photo

        self.perform_update(serializer)

        course = Course.objects.filter(pk=instance.course_id).first()
        serializer = CourseGetSerializer(course)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = instance.school.school_id
        remove_resp = remove_from_yandex(
            "/{}_school/{}_course".format(school_id, instance.course_id)
        )
        self.perform_destroy(instance)

        if remove_resp == "Error":
            return Response(
                {"error": "Запрашиваемый путь на диске не существует"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True)
    def clone(self, request, pk):
        """Клонирование курса\n
        Клонирование курса"""

        course = self.get_object()
        course_copy = course.make_clone(attrs={"name": f"{course.name}-копия"})
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())

    @action(detail=True)
    def sections(self, request, pk):
        """Данные по всем секциям курс\n
        Данные по всем секциям курса"""

        course = self.get_object()
        queryset = Course.objects.filter(course_id=course.pk)

        data = queryset.values(
            course=F("course_id"),
            course_name=F("name"),
            section_name=F("sections__name"),
            section=F("sections__section_id"),
            section_order=F("sections__order"),
        ).order_by("sections__order")
        result_data = dict(
            course_name=data[0]["course_name"],
            course_id=data[0]["course"],
            sections=[],
        )
        user = self.request.user
        lesson_progress = UserProgressLogs.objects.filter(user_id=user.pk)
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            result_data["sections"].append(
                {
                    "section_name": value["section_name"],
                    "section": value["section"],
                    "lessons": [],
                }
            )
            a = Homework.objects.filter(section=value["section"])
            b = Lesson.objects.filter(section=value["section"])
            c = SectionTest.objects.filter(section=value["section"])
            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["sections"][index]["lessons"].append(
                        {
                            "type": types[i[0]],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                            "completed": lesson_progress.filter(lesson_id=obj.baselesson_ptr_id).exists()
                        }
                    )
            result_data["sections"][index]["lessons"].sort(
                key=lambda x: x["order"] if x["order"] is not None else 0
            )
        return Response(result_data)

    @action(detail=True)
    def user_count_by_month(self, request, pk):
        """Кол-во новых пользователей курса за месяц\n
        Кол-во новых пользователей курса за месяц, по дефолту стоит текущий месяц,
        для конкретного месяца указываем параметр month_number=""
        """

        course = self.get_object()
        month_number = request.GET.get("month_number", datetime.now().month)

        queryset = StudentsGroup.objects.filter(
            course_id=course.pk, students__date_joined__month=month_number
        )

        datas = queryset.values(course=F("course_id")).annotate(
            students_sum=Count("students__id")
        )

        for data in datas:
            data["graphic_data"] = queryset.values(
                course=F("course_id"), date=F("students__date_joined__day")
            ).annotate(students_sum=Count("students__id"))

        page = self.paginate_queryset(datas)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(datas)

    @action(detail=True)
    def stats(self, request, pk):
        """Статистика всех студентов курса\n
        Статистика всех студентов курса"""

        course = self.get_object()
        queryset = StudentsGroup.objects.filter(course_id=course.pk)
        data = queryset.values(
            course=F("course_id"),
            email=F("students__email"),
            student_name=F("students__first_name"),
            student=F("students__id"),
            group=F("group_id"),
            last_active=F("students__date_joined"),
            update_date=F("students__date_joined"),
            ending_date=F("students__date_joined"),
        ).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            chekau=Count("course_id__sections__lessons__lesson_id")
            + Count("course_id__sections__homeworks__homework_id"),
            # progress=(Count("students__user_progresses__lesson__lesson_id"))
            #          / Count("course_id__sections__lessons__lesson_id"),
        )
        # Course.objects.filter(course_id=course.pk).values("course_id__sections__lessons_lesson_id",
        #                                                   "course_id__sections__section_tests__section_id")
        ## Выбрать все тесты, лессоны и хоумворки
        ## Далее проверить, что из них есть в юзер прогресс
        a = UserProgressLogs.objects.filter(
            lesson__section__course__course_id=course.pk,
            homework__section__course__course_id=course.pk,
            section_test__section__course__course_id=course.pk,
        ).aggregate(
            count_steps=Count("lesson__section__course__course_id")
            + Count("homework__section__course__course_id")
            + Count("section_test__section__course__course_id")
        )
        print(a)
        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                .values("user")
                .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += mark_sum // 10 if mark_sum is not None else 0
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

    @action(detail=True)
    def student_groups(self, request, pk):
        """Список всех групп курса\n
        Список всех групп курса"""

        queryset = StudentsGroup.objects.filter(course_id=pk)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = StudentsGroupSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudentsGroupSerializer(queryset, many=True)
        return Response(serializer.data)
