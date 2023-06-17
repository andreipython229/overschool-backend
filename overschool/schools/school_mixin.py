from django.http import Http404
from schools.models import School


class SchoolMixin:
    def dispatch(self, request, *args, **kwargs):
        school_name = kwargs.get(
            "school_name"
        )  # Получение имени школы из параметров URL
        # Проверка существования школы в базе данных
        if not School.objects.filter(name=school_name).exists():
            raise Http404("Школа не найдена")
        return super().dispatch(request, *args, **kwargs)
