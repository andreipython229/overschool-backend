from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import Referral, ReferralClick, School
from schools.school_mixin import SchoolMixin
from schools.serializers import ReferralClickSerializer, ReferralSerializer


class ReferralViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                Referral.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        return Referral.objects.filter(referrer_school=school_id)


class ReferralClickViewSet(
    WithHeadersViewSet, SchoolMixin, viewsets.ReadOnlyModelViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralClickSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                ReferralClick.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        return ReferralClick.objects.filter(school=school_id)


class ReferralClickRedirectView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, referral_code):
        # Поиск школы по реферальному коду
        school = get_object_or_404(School, referral_code=referral_code)

        # Запись клика
        ReferralClick.objects.create(
            school=school,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            timestamp=timezone.now(),
        )

        # URL для редиректа на страницу регистрации школы
        register_url = f"/create-school/?ref_code={referral_code}"

        return redirect(register_url)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip.strip()  # Очистка IP-адреса от пробелов
