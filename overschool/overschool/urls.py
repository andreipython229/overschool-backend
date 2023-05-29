from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from users.api_views import LoginView, LogoutView, SignupView,PasswordResetView, PasswordResetConfirmView

from .main_router import router

urlpatterns = [
                  path("admin/", admin.site.urls),
                  path("api/register/", SignupView.as_view(actions={"post": "post"}), name="register"),
                  path("api/login/", LoginView.as_view(actions={"post": "post"}), name="login"),
                  path("password/reset/", PasswordResetView.as_view(actions={"post": "post"}), name="password_reset"),
                  path("password/reset/confirm/", PasswordResetConfirmView.as_view(actions={"post": "post"}),
                       name="password_reset_confirm"),
                  path("api/logout/", LogoutView.as_view(actions={"get": "get"}), name="logout"),
                  path("api/", include(router.urls)),
                  path("api/chats/", include("chats.urls")),
                  re_path(
                      r"^account-confirm-email/(?P<key>[-:\w]+)/$",
                      TemplateView.as_view(),
                      name="account_confirm_email",
                  ),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
