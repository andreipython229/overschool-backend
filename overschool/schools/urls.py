from rest_framework import routers
from django.urls import path

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
    TariffViewSet,
    AddPaymentMethodViewSet,
    SchoolPaymentLinkViewSet,
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_headers", SchoolHeaderViewSet, basename="school_headers")
router.register("schools_tariff", TariffViewSet, basename="schools_tariff")
router.register("payment_method", AddPaymentMethodViewSet, basename='payment-method')
router.register("payment_link", SchoolPaymentLinkViewSet, basename='payment-link')

urlpatterns = router.urls

