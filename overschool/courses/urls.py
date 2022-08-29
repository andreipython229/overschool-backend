from rest_framework import routers

from courses.api_views import (
    CourseViewSet,
    AudioFileView,
    LessonViewSet,
    SectionViewSet,
    StudentsGroupViewSet,
    CourseHeaderViewSet,
)

router = routers.DefaultRouter()
router.register("course_header", CourseHeaderViewSet, basename="course_header")
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")
router.register("students_group", StudentsGroupViewSet, basename="students_group")

urlpatterns = router.urls
