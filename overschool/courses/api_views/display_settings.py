from courses.models import (
    UserLessonSettings,
    UserHomeworkSettings,
    UserTestSettings,
)
from rest_framework import generics

from .models import BaseLesson
from .serializers import BaseLessonSerializer


class UserLessonsView(generics.ListAPIView):
    serializer_class = BaseLessonSerializer

    def get_queryset(self):
        user = self.request.user
        user_lesson_settings = UserLessonSettings.objects.filter(user=user, show_lesson=True)
        user_homework_settings = UserHomeworkSettings.objects.filter(user=user, show_homework=True)
        user_test_settings = UserTestSettings.objects.filter(user=user, show_test=True)

        lesson_ids = user_lesson_settings.values_list('lesson_id', flat=True)
        homework_ids = user_homework_settings.values_list('homework_id', flat=True)
        test_ids = user_test_settings.values_list('test_id', flat=True)

        if lesson_ids.exists() or homework_ids.exists() or test_ids.exists():
            queryset = BaseLesson.objects.filter(id__in=lesson_ids | homework_ids | test_ids, active=True).distinct()
        else:
            queryset = BaseLesson.objects.none()

        return queryset
