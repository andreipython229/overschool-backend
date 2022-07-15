from rest_framework import routers

from courses.api_views import CourseViewSet, LessonViewSet, SectionViewSet

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("sections", SectionViewSet, basename="sections")

urlpatterns = router.urls
