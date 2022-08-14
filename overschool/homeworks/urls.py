from rest_framework import routers

from homeworks.api_views import HomeworkViewSet, HomeworkStatisticsView, UserHomework

router = routers.DefaultRouter()
router.register("homeworks", HomeworkViewSet, basename="homeworks")
router.register("homeworks_stats", HomeworkStatisticsView, basename="homeworks_stats")

urlpatterns = router.urls
