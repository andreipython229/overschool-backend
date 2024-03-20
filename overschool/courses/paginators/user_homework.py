from rest_framework import pagination
from rest_framework.response import Response


class UserHomeworkPagination(pagination.PageNumberPagination):
    page_size = 20
    max_page_size = 20
    page_query_param = "p"
    page_size_query_param = "s"
