from rest_framework import routers

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
    TariffViewSet,
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_headers", SchoolHeaderViewSet, basename="school_headers")
router.register("schools_tariff", TariffViewSet, basename="schools_tariff")
urlpatterns = router.urls
