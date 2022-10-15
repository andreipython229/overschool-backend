from rest_framework import routers

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_header", SchoolHeaderViewSet, basename="school_header")

urlpatterns = router.urls
