from rest_framework import pagination


class UserHomeworkPagination(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = 'limit'
    max_page_size = 25
    page_query_param = 'p'