from rest_framework.pagination import PageNumberPagination

from .constants import MAX_PAGE_SIZE, PAGE_SIZE


class PageLimitPagination(PageNumberPagination):
    """Кастомная пагинация для категорий и продуктов."""

    page_size = PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = MAX_PAGE_SIZE
