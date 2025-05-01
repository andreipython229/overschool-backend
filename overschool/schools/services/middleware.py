import json
import re
from urllib.parse import urlparse

import jwt
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from schools.models import Domain, School, TariffPlan
from users.models import User


class HttpResponseAccessDenied(HttpResponse):
    def __init__(self, data=None, message="Access Denied", *args, **kwargs):
        content = json.dumps(
            {
                "status": 451,
                "message": message,
                "data": data,
            },
            ensure_ascii=False,
        )
        super().__init__(
            content, status=451, content_type="application/json", *args, **kwargs
        )


class CheckTrialStatusMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/admin/"):
            return None

        user = request.user
        if user and user.is_authenticated:
            try:
                schools_owned = School.objects.filter(owner=user)
                schools_member = School.objects.filter(groups__user=user).distinct()

                for school in schools_owned:
                    school.check_trial_status()
                for school in schools_member:
                    school.check_trial_status()

            except Exception as e:
                pass

        return None

    def process_response(self, request, response):
        return response


class DomainAccessMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        r"/admin/.*" r"/api/login/",
        r"/api/school-by-domain/",
        r"/api/course_catalog/",
        r"/admin/",
        r"/api/token/refresh/",
        r"/api/token/verify/",
        r"/video/.+/block_video/\d+/",
        r"/api/.+/answers/\d+/",
    ]
    ALLOWED_DOMAINS = [
        "sandbox.coursehb.ru",
        "coursehb.ru",
        "sandbox.coursehb.ru",
        "platform.coursehb.ru",
        "localhost:8000",
        "localhost:3000",
        "127.0.0.1:8000",
        "91.211.248.84:8000",
    ]

    def process_request(self, request):
        if request.path.startswith("/admin/"):
            return None
        current_path = request.path

        if any(re.fullmatch(pattern, current_path) for pattern in self.EXCLUDED_PATHS):
            return None

        current_user = request.user

        domain = request.META.get("HTTP_X_ORIGIN")
        if domain:
            parsed_url = urlparse(domain)
            current_domain = parsed_url.netloc
        else:
            current_domain = request.get_host().split(":")[0]

        if current_domain in self.ALLOWED_DOMAINS:
            return None

        if current_user and current_user.is_authenticated:
            user_schools = set()
            user_schools.update(School.objects.filter(owner=current_user))
            user_schools.update(School.objects.filter(groups__user=current_user))

            if user_schools:
                # Ищем домен среди разрешенных для школ пользователя
                school_found = False
                for school in user_schools:
                    # Проверяем основной домен школы и связанные домены
                    if (
                        school.subdomain == current_domain
                        or Domain.objects.filter(
                            school=school, domain_name=current_domain
                        ).exists()
                    ):
                        school_found = True
                        # Проверяем тариф только если доступ через собственный домен (не основной и не из ALLOWED_DOMAINS)
                        is_custom_domain = (
                            current_domain != school.subdomain
                            and not Domain.objects.filter(
                                school=school, domain_name=current_domain, is_main=True
                            ).exists()
                        )

                        if (
                            is_custom_domain
                            and school.tariff.name != TariffPlan.SENIOR.value
                        ):
                            return HttpResponseForbidden(
                                "Доступ запрещен. Тариф школы не позволяет доступ через собственный домен."
                            )
                        # Если это основной домен школы или тариф Senior, доступ разрешен
                        return None

                # Если домен не найден среди разрешенных для пользователя
                if not school_found:
                    return HttpResponseForbidden(
                        "Доступ запрещен. Вы не можете получить доступ к этой школе через этот домен."
                    )
            else:
                return HttpResponseForbidden(
                    "Доступ запрещен. Пользователь не привязан к школе."
                )

        else:
            try:
                domain_entry = Domain.objects.get(
                    domain_name=current_domain, is_main=True
                )
                return None
            except Domain.DoesNotExist:
                return HttpResponseForbidden(
                    "Доступ запрещен. Требуется выполнить вход."
                )

    def process_response(self, request, response):
        return response
