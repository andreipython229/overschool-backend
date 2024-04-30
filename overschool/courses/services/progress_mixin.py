from courses.models import (
    BaseLesson,
    Homework,
    Lesson,
    Section,
    SectionTest,
    StudentsGroup,
)
from courses.models.students.user_progress import UserProgressLogs
from rest_framework import status
from rest_framework.response import Response


class LessonProgressMixin:
    def create_log(self, user, instance):
        try:
            UserProgressLogs.objects.get(user=user, lesson=instance)
        except UserProgressLogs.DoesNotExist:

            if isinstance(instance, Lesson):
                UserProgressLogs.objects.create(
                    user=user, lesson=instance, viewed=True, completed=True
                )
            else:
                UserProgressLogs.objects.create(user=user, lesson=instance, viewed=True)

    def check_lesson_progress(self, instance, user, baselesson):
        school = baselesson.section.course.school
        if user.groups.filter(
            group__name__in=[
                "Admin",
                "Teacher",
            ],
            school=school,
        ).exists():
            return None

        try:
            students_group = user.students_group_fk.get(
                course_id=baselesson.section.course
            )
        except StudentsGroup.MultipleObjectsReturned:
            return Response(
                {
                    "detail": "Один и тот же пользователь - не может быть в нескольких группах на курсе."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except StudentsGroup.DoesNotExist:
            return Response(
                {"detail": "Пользователь не состоит не в одной группе на этом курсе."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if students_group.group_settings.strict_task_order:
            print("students_group.group_settings.strict_task_order")
            try:
                # Если есть запись в логе - то отдаём урок
                UserProgressLogs.objects.get(user=user, lesson=instance)
            except UserProgressLogs.DoesNotExist:
                course_lessons = (
                    BaseLesson.objects.filter(
                        section__course_id=baselesson.section.course, active=True
                    )
                    .exclude(
                        lessonavailability__student=user,
                    )
                    .order_by("section__order", "order")
                )

                print("TEST LESSONS = ", course_lessons)
                # Если урок стоит первым в курсе - то отдаём урок
                if baselesson == course_lessons.first():
                    self.create_log(user=user, instance=instance)
                    return None
                # Проверяем является ли урок минимальным в секции
                is_minimum_order = (
                    not BaseLesson.objects.filter(
                        section=instance.section, order__lt=instance.order, active=True
                    )
                    .exclude(
                        lessonavailability__student=user,
                    )
                    .exists()
                )

                if is_minimum_order:
                    # берём последний урок из предыдущей секции
                    previous_section = (
                        Section.objects.filter(
                            course=instance.section.course,
                            order__lt=instance.section.order,
                        )
                        .order_by("-order")
                        .first()
                    )
                    previous_section_lessons = BaseLesson.objects.filter(
                        section=previous_section, active=True
                    )
                    last_lesson_previous_section = previous_section_lessons.order_by(
                        "-order"
                    ).first()
                    try:
                        # Если запись есть то отдаем урок и делаем запись
                        UserProgressLogs.objects.get(
                            user=user, lesson=last_lesson_previous_section.pk
                        )
                        self.create_log(user=user, instance=instance)
                        return None
                    except UserProgressLogs.DoesNotExist:
                        return Response(
                            {"detail": "Необходимо пройти предыдущие уроки."},
                            status=status.HTTP_403_FORBIDDEN,
                        )

                # Берем предыдущий урок по порядку поля order
                previous_lesson = (
                    BaseLesson.objects.filter(
                        section=instance.section, order__lt=instance.order, active=True
                    )
                    .exclude(
                        lessonavailability__student=user,
                    )
                    .order_by("-order")
                    .first()
                )
                try:
                    UserProgressLogs.objects.get(user=user, lesson=previous_lesson.pk)
                    self.create_log(user=user, instance=instance)
                except UserProgressLogs.DoesNotExist:
                    return Response(
                        {"detail": "Необходимо пройти предыдущие уроки."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        else:
            try:
                # Если есть запись в логе - то отдаём урок
                UserProgressLogs.objects.get(user=user, lesson=instance)
            except UserProgressLogs.DoesNotExist:
                # Если записи нет то создаём запись и отдаём урок
                self.create_log(user=user, instance=instance)

        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response("Урок не найден.")

        baselesson = BaseLesson.objects.get(pk=instance.baselesson_ptr_id)
        response = self.check_lesson_progress(instance, request.user, baselesson)
        if response is not None:
            return response
        return super().retrieve(request, *args, **kwargs)

    def check_viewed_and_progress_log(self, request, instance):
        if not instance:
            return Response("Урок не найден.")

        baselesson = BaseLesson.objects.get(pk=instance.baselesson_ptr_id)
        response = self.check_lesson_progress(instance, request.user, baselesson)
        return response
