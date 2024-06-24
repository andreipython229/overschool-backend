from django.http import Http404
from schools.models import School


class SchoolMixin:
    def dispatch(self, request, *args, **kwargs):
        # Вызов родительского dispatch для аутентификации пользователя
        response = super().dispatch(request, *args, **kwargs)

        school_name = kwargs.get("school_name")

        # Проверка существования школы в базе данных
        if not School.objects.filter(name=school_name).exists():
            raise Http404("Школа не найдена")

        # Проверка тарифа школы
        school = School.objects.get(name=school_name)
        user = request.user

        # Убедимся, что пользователь аутентифицирован
        if not user.is_authenticated:
            raise Http404("Пользователь не аутентифицирован")

        if school.tariff is None:  # Если тариф не оплачен
            if not user.groups.filter(group__name="Admin", school=school).exists():
                # Блокировка доступа к API для пользователей, кроме администраторов
                raise Http404("Тариф школы не оплачен")

        return response
