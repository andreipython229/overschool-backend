from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from courses.api_views import LessonUpdateViewSet
from users.api_views import (
    AccessDistributionView,
    ConfirmationView,
    LoginView,
    LogoutView,
    PasswordResetView,
    SignupSchoolOwnerView,
    SignupView,
    UserSchoolsView,

)
from utils.utils_view import subscribe_client, unsubscribe_client

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

                  path('api/subscribe-client/', subscribe_client, name='subscribe_client'),
                  path('api/unsubscribe-client/', unsubscribe_client, name='unsubscribe_client'),

                  path(
                      "api/code/confirm/",
                      ConfirmationView.as_view(actions={"post": "post"}),
                      name="code",
                  ),
                  path("api/reset-password/send-link/", PasswordResetView.as_view({"post": "send_reset_link"})),
                  path("api/reset-password/reset/", PasswordResetView.as_view({"post": "reset_password"})),

                  path(
                      "api/logout/",
                      LogoutView.as_view(actions={"get": "get"}),
                      name="logout",
                  ),
                  path(
                      "api/<str:school_name>/lesson_order/",
                      LessonUpdateViewSet.as_view(actions={"post": "shuffle_lessons"}),
                      name="lesson_order",
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


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["https", "http"]
        return schema


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
    generator_class=BothHttpAndHttpsSchemaGenerator,
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
