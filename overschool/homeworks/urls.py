from rest_framework import routers

from homeworks.api_views import HomeworkViewSet

router = routers.DefaultRouter()
router.register("homeworks", HomeworkViewSet, basename="homeworks")

urlpatterns = router.urls
