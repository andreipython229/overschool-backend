from courses.api_views import (
    AudioFileView,
    CourseViewSet,
    LessonViewSet,
    SectionViewSet,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")

urlpatterns = router.urls
# urlpatterns += [
#     path('audiofile/', AudioFileView.as_view())
# ]
