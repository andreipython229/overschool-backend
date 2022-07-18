from rest_framework import routers

from courses.api_views import CourseViewSet, LessonViewSet, SectionViewSet

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")

urlpatterns = router.urls
