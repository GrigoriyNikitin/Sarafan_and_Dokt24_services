from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from products.models import Category, Product, SubCategory

User = get_user_model()


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Все файлы, которые сохраняет Django, пишем во временную папку."""
    settings.MEDIA_ROOT = tmp_path


def _make_image(name: str = "test.jpg", size=(10, 10), color=(255, 0, 0)):
    """Создаёт валидный JPEG-файл для ImageField."""
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name,
        buffer.read(),
        content_type="image/jpeg",
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Электроника",
        slug="electronics",
        image=_make_image("category.jpg"),
    )


@pytest.fixture
def subcategory(db, category):
    return SubCategory.objects.create(
        name="Смартфоны",
        slug="smartphones",
        image=_make_image("subcategory.jpg"),
        category=category,
    )


@pytest.fixture
def product(db, subcategory):
    return Product.objects.create(
        name="iPhone 15",
        slug="iphone-15",
        image=_make_image("product.jpg"),
        subcategory=subcategory,
        price="999.99",
    )
