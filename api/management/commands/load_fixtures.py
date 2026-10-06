"""Загрузка фикстур каталога + генерация изображений-заглушек + демо-данные."""

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from products.models import (
    Basket,
    BasketProduct,
    Category,
    Product,
    SubCategory,
)

User = get_user_model()

FIXTURES = ("categories", "subcategories", "products")

CATEGORY_COLOR = (58, 130, 200)
SUBCATEGORY_COLOR = (60, 160, 110)
PRODUCT_COLOR = (220, 140, 60)


def _render_placeholder(text: str, color, size=(800, 800)) -> bytes:
    """Генерирует JPEG-заглушку с текстом по центру."""
    image = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(image)

    text = (text or "N/A")[:40]
    bbox = draw.textbbox((0, 0), text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size[0] - text_w) / 2, (size[1] - text_h) / 2),
        text,
        fill="white",
    )

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()


class Command(BaseCommand):
    help = (
        "Загружает фикстуры каталога, генерирует изображения и создаёт "
        "демо-пользователей с корзинами."
    )

    def handle(self, *args, **options):
        self.stdout.write("→ Загрузка фикстур...")
        call_command("loaddata", *FIXTURES, verbosity=0)
        self.stdout.write(self.style.SUCCESS("  ✔ фикстуры загружены"))

        self.stdout.write("→ Генерация изображений категорий...")
        self._generate_category_images()

        self.stdout.write("→ Генерация изображений подкатегорий...")
        self._generate_subcategory_images()

        self.stdout.write("→ Генерация изображений продуктов и миниатюр...")
        self._generate_product_images()

        self.stdout.write("→ Создание демо-пользователей и корзин...")
        self._create_users_and_baskets()

        self.stdout.write(self.style.SUCCESS("Готово."))

    # ---------- изображения ----------

    def _generate_category_images(self):
        for category in Category.objects.all():
            if self._file_exists(category.image):
                continue
            category.image.save(
                f"{category.slug}.jpg",
                ContentFile(_render_placeholder(category.name, CATEGORY_COLOR)),
            )

    def _generate_subcategory_images(self):
        for subcategory in SubCategory.objects.all():
            if self._file_exists(subcategory.image):
                continue
            subcategory.image.save(
                f"{subcategory.slug}.jpg",
                ContentFile(_render_placeholder(subcategory.name, SUBCATEGORY_COLOR)),
            )

    def _generate_product_images(self):
        for product in Product.objects.all():
            need_image = not self._file_exists(product.image)
            need_thumbs = not (
                self._file_exists(product.image_thumb)
                and self._file_exists(product.image_medium)
                and self._file_exists(product.image_large)
            )

            if need_image:
                product.image.save(
                    f"{product.slug}.jpg",
                    ContentFile(_render_placeholder(product.name, PRODUCT_COLOR)),
                    save=False,
                )
                product.save(update_fields=["image"])

            if need_image or need_thumbs:
                product._generate_sizes()

    @staticmethod
    def _file_exists(field) -> bool:
        return bool(field) and bool(field.name) and field.storage.exists(field.name)

    # ---------- пользователи и корзины ----------

    def _create_users_and_baskets(self):
        users = (
            ("admin", "admin@example.com", "admin12345", True, True),
            ("buyer", "buyer@example.com", "buyer12345", False, False),
        )

        for username, email, password, is_staff, is_superuser in users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"  создан пользователь: {username} / {password}")
            Basket.objects.get_or_create(user=user)

        basket = Basket.objects.filter(user__username="buyer").first()
        if basket and not basket.basket_items.exists():
            for product in Product.objects.all()[:3]:
                BasketProduct.objects.create(
                    basket=basket,
                    product=product,
                    amount=1,
                )
            self.stdout.write("  корзина buyer наполнена 3 товарами")
