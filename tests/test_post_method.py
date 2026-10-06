import pytest
from rest_framework import status

from products.models import Basket, BasketProduct

pytestmark = pytest.mark.django_db


BASKET_ADD_URL = "/api/basket/products/"


def test_basket_add_product_post(auth_client, user, product):
    """POST добавляет новый продукт в корзину."""
    response = auth_client.post(
        BASKET_ADD_URL,
        {
            "product": product.id,
            "amount": 2,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["amount"] == 2

    item = BasketProduct.objects.get(
        basket__user=user,
        product=product,
    )
    assert item.amount == 2


def test_basket_add_product_increases_amount(auth_client, user, product):
    """POST увеличивает количество, если продукт уже в корзине."""
    basket = Basket.objects.create(user=user)
    BasketProduct.objects.create(
        basket=basket,
        product=product,
        amount=1,
    )

    response = auth_client.post(
        BASKET_ADD_URL,
        {
            "product": product.id,
            "amount": 2,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    item = BasketProduct.objects.get(
        basket=basket,
        product=product,
    )
    assert item.amount == 3
