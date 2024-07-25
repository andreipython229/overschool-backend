from rest_framework import pagination
from rest_framework.response import Response


class UserHomeworkPagination(pagination.PageNumberPagination):
    page_size = 20
    max_page_size = 20
    page_query_param = "p"
    page_size_query_param = "s"

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if page_size is None:
            return None

        # Получаем номер страницы из параметра запроса
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number == '-1':
            # Если номер страницы -1, сохраняем все записи в атрибут, чтобы get_paginated_response мог их использовать
            self.page = None
            self.request = request
            self.display_page_controls = False
            return list(queryset)
        
        # Иначе используем стандартное поведение пагинации
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self.page is None:
            return Response(data)
        return super().get_paginated_response(data)