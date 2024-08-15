import json

import jwt
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from schools.models import Domain, School
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
        # Пропускаем запросы к админке
        if request.path.startswith("/admin/"):
            return None

        auth_header = request.META.get("HTTP_AUTHORIZATION", None)
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]

            try:
                payload = jwt.decode(
                    access_token,
                    settings.SIMPLE_JWT["SIGNING_KEY"],
                    algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
                )
                user = User.objects.get(pk=payload.get("user_id"))
                request.user = user

                # Вызываем метод check_trial_status() для аутентифицированного пользователя
                if user.is_authenticated:
                    try:
                        for school in School.objects.filter(owner=user):
                            school.check_trial_status()

                        for school in School.objects.filter(groups__user=user):
                            school.check_trial_status()
                    except School.DoesNotExist:
                        pass
            except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
                pass

    def process_response(self, request, response):
        return response


class DomainAccessMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = ["/api/login/", "/admin/"]
    ALLOWED_DOMAINS = [
        "sandbox.coursehb.ru",
        "coursehb.ru",
        "sandbox.coursehb.ru",
        "platform.coursehb.ru",
        "localhost:8000",
        "localhost:3000",
        "127.0.0.1:8000",
        "45.135.234.21:8000",
        "45.135.234.21:8000",
    ]

    def process_request(self, request):
        current_path = request.path

        # Исключаем страницы логина и другие страницы
        if any(current_path.startswith(path) for path in self.EXCLUDED_PATHS):
            return None

        auth_header = request.META.get("HTTP_AUTHORIZATION", None)
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    access_token,
                    settings.SIMPLE_JWT["SIGNING_KEY"],
                    algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
                )
                user = User.objects.get(pk=payload.get("user_id"))
                request.user = user
            except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
                request.user = None
        else:
            request.user = None

        current_user = request.user
        current_domain = request.get_host()  # Получение текущего домена из запроса
        print(current_domain)

        # Проверка для общего домена
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
                print(school_domains)
                print(current_domain)
                if not any(
                    school_domain.domain_name == current_domain
                    for school_domain in school_domains
                ):
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
