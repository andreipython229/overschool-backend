from rest_framework import routers

from courses.api_views import (
    CourseViewSet,
    CreateAudioFileView,
    GetAudioFileView,
    LessonViewSet,
    SectionViewSet,
)

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("create-audiofile", CreateAudioFileView, basename="create-audiofile")
router.register("get-audiofile", GetAudioFileView, basename="get-audiofile")

urlpatterns = router.urls
