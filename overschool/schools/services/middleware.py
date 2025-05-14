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
        host = request.META.get("HTTP_HOST")
        if domain:
            parsed_url = urlparse(domain)
            current_domain = parsed_url.netloc
        elif host:
            current_domain = host
        else:
            current_domain = None

            # Проверка для общего домена
        print(current_domain)
        if current_domain in self.ALLOWED_DOMAINS:
            return None

        if current_user and current_user.is_authenticated:
            # Получаем все школы, к которым пользователь имеет доступ (как владелец или через группы)
            user_schools = set()
            user_schools.update(School.objects.filter(owner=current_user))
            user_schools.update(School.objects.filter(groups__user=current_user))

            # Если есть школы у пользователя
            if user_schools:
                # Проверяем домены всех школ пользователя
                school_domains = Domain.objects.filter(school__in=user_schools)

                for school_domain in school_domains:
                    if school_domain.domain_name == current_domain:
                        # Проверяем, что у школы тариф Senior
                        if school_domain.school.tariff.name != TariffPlan.SENIOR.value:
                            return HttpResponseForbidden(
                                "Доступ запрещен. Тариф школы не позволяет доступ через собственный домен."
                            )
                        return None

                return HttpResponseForbidden(
                    "Доступ запрещен. Вы не можете получить доступ к этой школе через этот домен."
                )
            else:
                # Проверяем, существует ли домен и привязан ли он к школе для неавторизованных пользователей
                if not Domain.objects.filter(domain_name=current_domain).exists():
                    return HttpResponseForbidden(
                        "Доступ запрещен. Необходимо выполнить вход."
                    )

    def process_response(self, request, response):
        return response
