from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from utils.utils_view import subscribe_client, unsubscribe_client, recalculate_cost, get_next_payment_time
from users.api_views import (
    AccessDistributionView,
    ConfirmationView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    SignupSchoolOwnerView,
    SignupView,
    UserSchoolsView,
)

from .main_router import router, school_router, user_router

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/register/",
        SignupView.as_view(actions={"post": "post"}),
        name="register",
    ),
    path(
        "api/register-school-owner/",
        SignupSchoolOwnerView.as_view(actions={"post": "post"}),
        name="register_school_owner",
    ),
    path(
        "api/<str:school_name>/access-distribution/",
        AccessDistributionView.as_view(actions={"post": "post", "delete": "delete"}),
        name="access_distribution",
    ),
    path(
        "api/login/",
        LoginView.as_view(actions={"post": "post"}),
        name="login",
    ),
    path(
        "api/user-schools/",
        UserSchoolsView.as_view(actions={"get": "list"}),
        name="user_schools",
    ),

    path('api/subscribe-client/<int:user_id>/', subscribe_client, name='subscribe_client'),
    path('api/unsubscribe-client/<int:user_id>/', unsubscribe_client, name='unsubscribe_client'),
    path('api/recalculate-cost/<int:user_id>/', recalculate_cost, name='recalculate_cost'),
    path('api/get-next-payment-time/<int:user_id>/', get_next_payment_time, name='get_next_payment_time'),

    path(
        "api/code/confirm/",
        ConfirmationView.as_view(actions={"post": "post"}),
        name="code",
    ),
    path(
        "api/password/reset/",
        PasswordResetView.as_view(actions={"post": "post"}),
        name="password_reset",
    ),
    path(
        "api/password/reset/confirm/",
        PasswordResetConfirmView.as_view(actions={"post": "post"}),
        name="password_reset_confirm",
    ),
    path(
        "api/logout/",
        LogoutView.as_view(actions={"get": "get"}),
        name="logout",
    ),
    path("api/chats/", include("chats.urls")),
    path("api/", include(user_router.urls)),
    path("api/", include(school_router.urls)),
    path("api/<str:school_name>/", include(router.urls)),
    re_path(
        r"^account-confirm-email/(?P<key>[-:\w]+)/$",
        TemplateView.as_view(),
        name="account_confirm_email",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
