import os
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from PIL import Image

from .constants import (
    AMOUNT_MAX_VALUE,
    AMOUNT_MIN_VALUE,
    NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
)

IMAGE_SIZES = (
    ("thumb", 150, 150),
    ("medium", 400, 400),
    ("large", 1000, 1000),
)


User = get_user_model()


class Category(models.Model):
    """Модель для категорий."""

    name = models.CharField(
        max_length=NAME_MAX_LENGTH, unique=True, verbose_name="Название категории"
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Идентификатор категории",
        help_text="Разрешены символы латиницы, цифры, дефис и подчёркивание.",
    )
    image = models.ImageField(
        upload_to="categories/",
        verbose_name="Изображение категории",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Модель для подкатегорий."""

    name = models.CharField(
        max_length=NAME_MAX_LENGTH, unique=True, verbose_name="Название подкатегории"
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Идентификатор подкатегории",
        help_text="Разрешены символы латиницы, цифры, дефис и подчёркивание.",
    )
    image = models.ImageField(
        upload_to="subcategories/",
        verbose_name="Изображение подкатегории",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name="Категория",
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("category", "name"), name="unique_category_name"
            ),
        )
        ordering = ("name",)
        verbose_name = "подкатегория"
        verbose_name_plural = "Подкатегории"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель для продуктов."""

    name = models.CharField(
        max_length=NAME_MAX_LENGTH, db_index=True, verbose_name="Название продукта"
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Идентификатор продукта",
        help_text="Разрешены символы латиницы, цифры, дефис и подчёркивание.",
    )
    image = models.ImageField(
        upload_to="products/original/",
        verbose_name="Изображение продукта",
    )
    # Генерируются автоматически в save()
    image_thumb = models.ImageField(
        upload_to="products/thumb/",
        blank=True,
        editable=False,
        verbose_name="Миниатюра (150×150)",
    )
    image_medium = models.ImageField(
        upload_to="products/medium/",
        blank=True,
        editable=False,
        verbose_name="Средний размер (400×400)",
    )
    image_large = models.ImageField(
        upload_to="products/large/",
        blank=True,
        editable=False,
        verbose_name="Большой размер (1000×1000)",
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Подкатегория",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена продукта",
    )

    @property
    def category(self):
        """Доступ к категории через подкатегорию."""
        return self.subcategory.category

    class Meta:
        ordering = ("name",)
        verbose_name = "продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new_image = self._state.adding or self._image_changed()
        super().save(*args, **kwargs)

        if self.image and is_new_image:
            self._generate_sizes()

    def _image_changed(self) -> bool:
        """
        Проверяем, изменилось ли поле image с момента последнего сохранения.
        """

        if not self.pk:
            return True
        old = Product.objects.filter(pk=self.pk).only("image").first()
        return not old or old.image != self.image

    def _generate_sizes(self):
        """Создаёт thumb, medium, large из оригинала."""
        self.image.open()
        with Image.open(self.image) as img:
            img = img.convert("RGB")

            for suffix, max_w, max_h in IMAGE_SIZES:
                img_copy = img.copy()
                img_copy.thumbnail((max_w, max_h), Image.LANCZOS)

                buffer = BytesIO()
                img_copy.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                filename = f"{os.path.splitext(os.path.basename(self.image.name))[0]}_{
                    suffix
                }.jpg"
                field = getattr(self, f"image_{suffix}")

                # удаляем старый файл, если был
                if field and hasattr(field, "delete"):
                    field.delete(save=False)

                field.save(filename, ContentFile(buffer.read()), save=False)

        # сохраняем только обновлённые поля картинок, без рекурсии
        super().save(update_fields=["image_thumb", "image_medium", "image_large"])


class Basket(models.Model):
    """Модель продуктовой корзины."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="basket",
        verbose_name="Пользователь",
    )
    products = models.ManyToManyField(
        Product,
        through="BasketProduct",
        related_name="baskets",
        verbose_name="Продукты",
    )

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.user}"


class BasketProduct(models.Model):
    """Промежуточная модель: продукт + количество в конкретной корзине."""

    basket = models.ForeignKey(
        Basket,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Корзина",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Продукт",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество продукта в корзине",
        validators=(
            MinValueValidator(AMOUNT_MIN_VALUE),
            MaxValueValidator(AMOUNT_MAX_VALUE),
        ),
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("basket", "product"), name="unique_basket_product"
            ),
        )
        verbose_name = "продукт в корзине"
        verbose_name_plural = "Продукты в корзине"

    def __str__(self):
        return f"{self.basket.user}: {self.product} × {self.amount}"
