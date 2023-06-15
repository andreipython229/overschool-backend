from courses.models import Lesson, BaseLesson, Section, Homework, SectionTest
from rest_framework import status
from rest_framework.response import Response
from courses.models.students.user_progress import UserProgressLogs

class LessonProgressMixin:

    def create_log(self, user, instance):
        if type(instance) == Lesson:
            UserProgressLogs.objects.create(user=user, lesson=instance)

    def check_lesson_progress(self, instance, user, baselesson):
        try:
            students_group = user.students_group_fk.get(course_id=baselesson.section.course)
        except Exception as e:
            return Response({"detail": "Один и тот же пользователь - не может быть в нескольких группах на курсе."}, status=status.HTTP_403_FORBIDDEN)

        if students_group.group_settings.strict_task_order:
            try:
                # Если есть запись в логе - то отдаём урок
                UserProgressLogs.objects.get(user=user, lesson=instance)
            except UserProgressLogs.DoesNotExist:
                course_lessons = BaseLesson.objects.filter(section__course_id=baselesson.section.course).order_by('section__order', 'order')

                # Если урок стоит первым в курсе - то отдаём урок
                if baselesson == course_lessons.first():
                    self.create_log(user=user, instance=instance)
                    return None
                # Проверяем является ли урок минимальным в секции
                is_minimum_order = not BaseLesson.objects.filter(section=instance.section, order__lt=instance.order).exists()
                if is_minimum_order:
                    # берём последний урок из предыдущей секции
                    previous_section = Section.objects.filter(course=instance.section.course,
                                                              order__lt=instance.section.order).order_by('-order').first()
                    previous_section_lessons = BaseLesson.objects.filter(section=previous_section)
                    last_lesson_previous_section = previous_section_lessons.order_by('-order').first()
                    try:
                        # Если запись есть то отдаем урок и делаем запись
                        UserProgressLogs.objects.get(user=user, lesson=last_lesson_previous_section.pk)
                        self.create_log(user=user, instance=instance)
                        return None
                    except UserProgressLogs.DoesNotExist:
                        return Response({"detail": "Необходимо проити предыдущие уроки."}, status=status.HTTP_403_FORBIDDEN)

                # Берем предыдущий урок по порядку поля order
                previous_lesson = BaseLesson.objects.filter(section=instance.section,
                                                            order__lt=instance.order).order_by('-order').first()
                try:
                    UserProgressLogs.objects.get(user=user, lesson=previous_lesson.pk)
                    self.create_log(user=user, instance=instance)
                except UserProgressLogs.DoesNotExist:
                    return Response({"detail": "Необходимо проити предыдущие уроки."}, status=status.HTTP_403_FORBIDDEN)
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
        user = self.request.user

        baselesson = BaseLesson.objects.get(pk=instance.baselesson_ptr_id)
        response = self.check_lesson_progress(instance, user, baselesson)
        if response is not None:
            return response
        return super().retrieve(request, *args, **kwargs)