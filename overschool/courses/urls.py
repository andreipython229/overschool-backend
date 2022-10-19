from courses.api_views import (
    CourseViewSet,
    AudioFileView,
    LessonViewSet,
    SectionViewSet,
    StudentsGroupViewSet,
    StudentsTableInfoViewSet,
)
from rest_framework import routers

router = routers.DefaultRouter()

router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")
router.register("students_group", StudentsGroupViewSet, basename="students_group")
router.register("students_table_info", StudentsTableInfoViewSet, basename="students_table_info")

urlpatterns = router.urls
