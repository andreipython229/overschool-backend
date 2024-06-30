from rest_framework import routers
from django.urls import path

from schools.api_views import (
    SchoolViewSet,
    SchoolHeaderViewSet,
    TariffViewSet,
    AddPaymentMethodViewSet,
    SchoolPaymentLinkViewSet,
    ProdamusPaymentLinkViewSet,
    SchoolStudentsTableSettingsViewSet,
    SchoolMeetingsViewSet,
    DomainViewSet,
    UnconfiguredDomainViewSet,
    ConfiguredDomainViewSet,
    NewsletterTemplateViewSet
)

router = routers.DefaultRouter()
router.register("schools", SchoolViewSet, basename="schools")
router.register("school_headers", SchoolHeaderViewSet, basename="school_headers")
router.register("schools_tariff", TariffViewSet, basename="schools_tariff")
router.register("payment_method", AddPaymentMethodViewSet, basename='payment-method')
router.register("payment_link", SchoolPaymentLinkViewSet, basename='payment-link'),
router.register("prodamus_payment_link", ProdamusPaymentLinkViewSet, basename='prodamus-payment-link')
router.register("school_students_table_settings", SchoolStudentsTableSettingsViewSet, basename='school_students_table_settings')
router.register(r'unconfigured_domains', UnconfiguredDomainViewSet, basename='unconfigured_domains')
router.register(r'configured_domains', ConfiguredDomainViewSet, basename='configured_domains')
router.register(r'(?P<school_name>\w+)/newsletter_templates', NewsletterTemplateViewSet, basename='newsletter_templates')

router_meetings = routers.DefaultRouter()
router_meetings.register("school_meetings", SchoolMeetingsViewSet, basename='school_meetings')

router_domain = routers.DefaultRouter()
router_domain.register("school_domain", DomainViewSet, basename='school_domain')

urlpatterns = router.urls

