from rest_framework import routers

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
    TariffViewSet,
    AddPaymentMethodViewSet,
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_headers", SchoolHeaderViewSet, basename="school_headers")
router.register("schools_tariff", TariffViewSet, basename="schools_tariff")
router.register("payment_method", AddPaymentMethodViewSet, basename='payment-method')

urlpatterns = router.urls
