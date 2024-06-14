import json

from django.conf import settings
from django.http import HttpResponse
from jwt import InvalidTokenError, decode
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


class CheckTrialStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get(settings.ACCESS)
        if access_token:
            try:
                payload = decode(
                    access_token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user = User.objects.get(pk=payload.get("sub"))
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
            except InvalidTokenError:
                pass

        response = self.get_response(request)
        return response


class DomainAccessMiddleware:
    EXCLUDED_PATHS = ["/api/login/"]
    ALLOWED_DOMENS = [
        "dev.overschool.by",
        "apidev.overschool.by",
        "dev.api.overschool.by",
        "apidev.overschool.by:8000",
        "sandbox.overschool.by",
        "overschool.by",
        "localhost:8000",
        "127.0.0.1:8000",
        "45.87.219.3:8000",
        "45.135.234.137:8000",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_path = request.path

        # Исключаем страницы логина и другие страницы
        if current_path in DomainAccessMiddleware.EXCLUDED_PATHS:
            response = self.get_response(request)
            return response

        access_token = request.COOKIES.get(settings.ACCESS)
        if access_token:
            try:
                payload = decode(
                    access_token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user = User.objects.get(pk=payload.get("sub"))
                request.user = user

            except InvalidTokenError:
                request.user = None
        else:
            request.user = None

        current_user = request.user
        current_domain = request.get_host()  # Получение текущего домена из запроса

        if current_user and current_user.is_authenticated:
            # Получаем все школы, к которым пользователь имеет доступ (как владелец или через группы)
            user_schools = set()
            user_schools.update(School.objects.filter(owner=current_user))
            user_schools.update(School.objects.filter(groups__user=current_user))

            # Если есть школы у пользователя
            if user_schools:
                # Проверяем домены всех школ пользователя
                school_domains = Domain.objects.filter(school__in=user_schools)
                if not any(
                    school_domain.domain_name == current_domain
                    for school_domain in school_domains
                ) and (current_domain not in DomainAccessMiddleware.ALLOWED_DOMENS):
                    return HttpResponseAccessDenied(
                        message="Доступ запрещен. Вы не можете получить доступ к этой школе через этот домен."
                    )
        else:
            # Проверяем, существует ли домен и привязан ли он к школе для неавторизованных пользователей
            if current_domain not in DomainAccessMiddleware.ALLOWED_DOMENS:
                return HttpResponseAccessDenied(
                    message="Доступ запрещен. Необходимо выполнить вход."
                )

        response = self.get_response(request)
        return response
