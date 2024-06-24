from common_services.api_views import (
    PaymentNotificationView,
    SubscribeClientView,
    UnsubscribeClientView,
)
from courses.api_views import (
    BlockUpdateViewSet,
    CourseAppealsViewSet,
    CourseCatalogViewSet,
    LessonUpdateViewSet,
    SectionUpdateViewSet,
    TrainingDurationViewSet,
)
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
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from schools.api_views import SchoolTasksViewSet
from users.api_views import (
    AccessDistributionView,
    AllUsersViewSet,
    EmailValidateView,
    ForgotPasswordView,
    GetCertificateView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetView,
    SendPasswordView,
    SignupSchoolOwnerView,
    SignupView,
    TariffSchoolOwner,
    TokenValidateView,
    UserSchoolsView,
)

from .main_router import (
    appeal_router,
    catalogs_router,
    notifications_router,
    router,
    school_router,
    user_router,
    videos_router,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "api/<str:school_name>/all_users/",
        AllUsersViewSet.as_view(actions={"get": "list"}),
        name="all_users",
    ),
    path(
        "api/<str:school_name>/current_tariff/",
        TariffSchoolOwner.as_view(actions={"get": "get"}),
        name="current_tariff",
    ),
    path(
        "api/<str:school_name>/school_tasks/",
        SchoolTasksViewSet.as_view(actions={"get": "get"}),
        name="school_tasks",
    ),
    path(
        "api/register_user/",
        SendPasswordView.as_view(actions={"post": "post"}),
        name="register_user",
    ),
    path(
        "api/register/",
        SignupView.as_view(actions={"post": "post"}),
        name="register",
    ),
    path(
        "api/forgot_password/",
        ForgotPasswordView.as_view(actions={"post": "post"}),
        name="forgot_password",
    ),
    path(
        "api/course-appeals/",
        CourseAppealsViewSet.as_view(actions={"post": "post"}),
        name="course-appeals",
    ),
    path(
        "api/token-validate/<int:user_id>/<str:token>/",
        TokenValidateView.as_view(actions={"get": "get"}),
        name="token-validate",
    ),
    path(
        "api/email-confirm/<str:token>/",
        EmailValidateView.as_view(actions={"get": "get"}),
        name="email-confirm",
    ),
    path(
        "api/password-reset/",
        PasswordResetView.as_view(actions={"post": "post"}),
        name="password-reset",
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
    path(
        "api/<str:school_name>/subscribe/",
        SubscribeClientView.as_view(actions={"post": "post"}),
        name="subscribe-client",
    ),
    path(
        "api/<str:school_name>/unsubscribe/",
        UnsubscribeClientView.as_view(actions={"post": "post"}),
        name="unsubscribe-client",
    ),
    path(
        "api/payment-notification/",
        PaymentNotificationView.as_view(actions={"post": "post"}),
        name="payment_notification",
    ),
    path(
        "api/change-password/",
        PasswordChangeView.as_view(actions={"post": "change_password"}),
    ),
    path(
        "api/logout/",
        LogoutView.as_view(actions={"post": "post"}),
        name="logout",
    ),
    path(
        "api/<str:school_name>/lesson_order/",
        LessonUpdateViewSet.as_view(actions={"post": "shuffle_lessons"}),
        name="lesson_order",
    ),
    path(
        "api/<str:school_name>/block_order/",
        BlockUpdateViewSet.as_view(actions={"post": "shuffle_blocks"}),
        name="block_order",
    ),
    path(
        "api/<str:school_name>/section_order/",
        SectionUpdateViewSet.as_view(actions={"post": "shuffle_sections"}),
        name="section_order",
    ),
    path(
        "api/<str:school_name>/students_training_duration/",
        TrainingDurationViewSet.as_view(actions={"post": "post", "get": "list"}),
        name="students_training_duration",
    ),
    path("api/certificate/", GetCertificateView.as_view(), name="get_certificate"),
    path("api/chats/", include("chats.urls")),
    path("api/chatgpt/", include("chatgpt.urls")),
    path("api/", include(catalogs_router.urls)),
    path("api/", include(user_router.urls)),
    path("api/", include(school_router.urls)),
    path("video/<str:school_name>/", include(videos_router.urls)),
    path("api/<str:school_name>/", include(router.urls)),
    path("api/<str:school_name>/", include(appeal_router.urls)),
    path("api/tg_notification/", include(notifications_router.urls)),
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
