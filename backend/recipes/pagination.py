from rest_framework.pagination import PageNumberPagination


class PageLimitNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
