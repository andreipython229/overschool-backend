from rest_framework import routers

from courses.api_views import (
    AudioFileView,
    CourseViewSet,
    LessonViewSet,
    SectionViewSet,
)

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")

urlpatterns = router.urls
