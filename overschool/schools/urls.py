from rest_framework import routers
from django.urls import path

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
    TariffViewSet,
    AddPaymentMethodViewSet,
    SchoolPaymentLinkViewSet,
    ProdamusPaymentLinkViewSet
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_headers", SchoolHeaderViewSet, basename="school_headers")
router.register("schools_tariff", TariffViewSet, basename="schools_tariff")
router.register("payment_method", AddPaymentMethodViewSet, basename='payment-method')
router.register("payment_link", SchoolPaymentLinkViewSet, basename='payment-link'),
router.register("prodamus_payment_link", ProdamusPaymentLinkViewSet, basename='prodamus-payment-link')
router.register("school_students_table_settings", SchoolStudentsTableSettingsViewSet, basename='school_students_table_settings')

urlpatterns = router.urls

