from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.paginators import RatingPagination
from courses.serializers import StudentRatingSerializer
from django.core.exceptions import PermissionDenied
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import User, UserGroup


class StudentRatingViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentRatingSerializer
    pagination_class = RatingPagination

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        return School.objects.get(name=school_name)

    def get_permissions(self, *args, **kwargs):
        school = self.get_school()
        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if self.action in ["all_rating"]:
            if user.groups.filter(
                group__name__in=[
                    "Student",
                    "Admin",
                    "Teacher",
                ],
                school=school,
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if self.action in ["individual_rating"]:
            # Разрешения для просмотра личного рейтинга студента (Только Student)
            if user.groups.filter(
                group__name__in=[
                    "Student",
                ],
                school=school,
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    @action(detail=False, methods=["get"])
    def individual_rating(self, request, **kwargs):
        """
        Индивидуальный рейтинг студента,сделавшего запрос\n
        """
        user = request.user

        completed_lessons = None
        top_by_lessons_num = None
        available_courses = None
        top_by_courses_num = None
        rating_dict = {}

        students_by_lessons, students_by_courses = self.generate_rating(True, True)

        print(students_by_lessons)

        student_in_selection_by_lessons = students_by_lessons.filter(id=user.id).first()

        if student_in_selection_by_lessons:
            completed_lessons = student_in_selection_by_lessons.completed_lessons
            if completed_lessons > 0:
                top_by_lessons_num = students_by_lessons.exclude(
                    completed_lessons__lt=completed_lessons
                ).count()

        print(students_by_courses.values("available_courses", "email"))

        student_in_selection_by_courses = students_by_courses.filter(id=user.id).first()

        if student_in_selection_by_courses:
            available_courses = student_in_selection_by_courses.available_courses
            if available_courses > 0:
                top_by_courses_num = students_by_courses.exclude(
                    available_courses__lt=available_courses
                ).count()

        rating_dict["completed_lessons"] = completed_lessons
        rating_dict["top_by_lessons_num"] = top_by_lessons_num
        rating_dict["available_courses"] = available_courses
        rating_dict["top_by_courses_num"] = top_by_courses_num

        return Response(rating_dict)

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "lessons_flag",
                openapi.IN_QUERY,
                description="Рейтинг по пройденным занятиям",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "courses_flag",
                openapi.IN_QUERY,
                description="Рейтинг по количеству доступных курсов",
                type=openapi.TYPE_BOOLEAN,
            ),
        ],
    )
    def all_rating(self, request, **kwargs):
        """
        Рейтинг студентов школы по пройденным занятиям или доступным курсам в школе\n
        """
        lessons_flag = request.query_params.get("lessons_flag")
        courses_flag = request.query_params.get("courses_flag")

        if lessons_flag and courses_flag:
            return Response(
                {
                    "error": "Можно получить рейтинг либо по пройденным занятиям, либо по доступным курсам"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        top_students = User.objects.none()

        students_by_lessons, students_by_courses = self.generate_rating(
            lessons_flag, courses_flag
        )

        if lessons_flag:
            top_students = students_by_lessons.exclude(completed_lessons=0)[:1000]

        if courses_flag:
            top_students = students_by_courses.exclude(available_courses=0)[:1000]

        # Применяем пагинацию
        page = self.paginate_queryset(top_students)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(top_students, many=True)

        return Response(serializer.data)

    def generate_rating(self, lessons_flag, courses_flag):
        """Формирует рейтинг студентов по пройденным занятиям и доступным курсам в школе"""

        students_by_lessons = User.objects.none()
        students_by_courses = User.objects.none()

        school = self.get_school()
        student_of_cur_school_role = UserGroup.objects.filter(
            group__name="Student", school=school, user=OuterRef("id")
        ).values("id")[:1]

        if lessons_flag:
            students_by_lessons = (
                User.objects.filter(groups=Subquery(student_of_cur_school_role))
                .annotate(
                    completed_lessons=Count(
                        "user_progresses",
                        filter=Q(
                            user_progresses__lesson__section__course__school=school,
                            user_progresses__completed=True,
                        ),
                    )
                )
                .order_by("-completed_lessons")
            )

        if courses_flag:
            students_by_courses = (
                User.objects.filter(groups=Subquery(student_of_cur_school_role))
                .annotate(
                    available_courses=Count(
                        "students_group_fk",
                        filter=Q(students_group_fk__course_id__school=school),
                    )
                )
                .order_by("-available_courses")
            )

        return students_by_lessons, students_by_courses
