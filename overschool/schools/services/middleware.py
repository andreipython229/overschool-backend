from django.conf import settings
from jwt import InvalidTokenError, decode
from schools.models import School
from users.models import User


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
