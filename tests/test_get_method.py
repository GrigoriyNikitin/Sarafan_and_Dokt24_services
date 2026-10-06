import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_category_list_get(api_client, category):
    """Проверяет эндпоинт списка категорий."""
    response = api_client.get("/api/categories/")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Если включена пагинация PageLimitPagination
    assert data["count"] == 1
    assert data["results"][0]["name"] == category.name
    assert data["results"][0]["slug"] == category.slug


def test_product_list_get(api_client, product):
    """Проверяет эндпоинт списка продуктов."""
    response = api_client.get("/api/products/")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["count"] == 1
    assert data["results"][0]["name"] == product.name
    assert data["results"][0]["slug"] == product.slug
