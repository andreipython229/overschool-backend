from rest_framework import pagination


class UserHomeworkPagination(pagination.PageNumberPagination):
    page_size = 25
    max_page_size = 25
    page_query_param = 'p'
    page_size_query_param = 's'



