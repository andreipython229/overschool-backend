from rest_framework import routers

from homeworks.api_views import HomeworkViewSet, HomeworkStatisticsView, UserHomeworkViewSet

router = routers.DefaultRouter()
router.register("homeworks", HomeworkViewSet, basename="homeworks")
router.register("homeworks_stats", HomeworkStatisticsView, basename="homeworks_stats")
router.register("user_homeworks", UserHomeworkViewSet, basename="user_homeworks")

urlpatterns = router.urls
