from rest_framework import routers

from courses.api_views import (
    CourseViewSet,
    AudioFileView,
    LessonViewSet,
    SectionViewSet,
    StudentsGroupViewSet,
    SchoolHeaderViewSet,
)

router = routers.DefaultRouter()
router.register("school_header", SchoolHeaderViewSet, basename="school_header")
router.register("course", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")
router.register("students_group", StudentsGroupViewSet, basename="students_group")

urlpatterns = router.urls
