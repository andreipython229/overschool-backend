from django.http import Http404
from schools.models import School


class SchoolMixin:
    def dispatch(self, request, *args, **kwargs):
        school_name = kwargs.get("school_name")

        try:
            school = School.objects.get(name=school_name)
        except School.DoesNotExist:
            raise Http404("Школа не найдена")

        user = request.user

        if not user or not user.is_authenticated:
            print(user)
            raise Http404("Пользователь не аутентифицирован")

        if school.tariff is None:
            if not user.groups.filter(group__name="Admin", school=school).exists():
                raise Http404("Тариф школы не оплачен")

        request.school = school

        return super().dispatch(request, *args, **kwargs)
