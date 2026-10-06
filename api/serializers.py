from rest_framework import serializers

from products.models import Basket, BasketProduct, Category, Product, SubCategory

from .constants import AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE


class SubCategorySerializer(serializers.ModelSerializer):
    """Сериализатор подкатегорий."""

    class Meta:
        model = SubCategory
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий."""

    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "image", "subcategories")


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор продуктов."""

    images = serializers.SerializerMethodField()
    subcategory = serializers.StringRelatedField(read_only=True)
    category = serializers.CharField(source="subcategory.category.name", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "category",
            "subcategory",
            "images",
        )

    def get_images(self, obj):
        """Возвращает список URL всех изображений продукта."""
        request = self.context.get("request")
        result = []

        for field_name in ("image_thumb", "image_medium", "image_large"):
            image_field = getattr(obj, field_name, None)
            if not image_field:
                continue

            url = image_field.url
            if request is not None:
                url = request.build_absolute_uri(url)
            result.append(url)

        return result


class BasketProductSerializer(serializers.ModelSerializer):
    """Сериализатор продуктов внутри корзины."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = BasketProduct
        fields = ("product_name", "price", "amount")


class BasketSerializer(serializers.ModelSerializer):
    """Сериализатор продуктовых корзин."""

    user = serializers.StringRelatedField(read_only=True)
    products = BasketProductSerializer(source="basket_items", many=True, read_only=True)
    total_count = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = (
            "user",
            "products",
            "total_count",
            "total_price",
        )

    def _totals(self, obj):
        if not hasattr(obj, "_totals_cache"):
            items = list(obj.basket_items.all())
            obj._totals_cache = {
                "count": sum(item.amount for item in items),
                "price": sum(item.amount * item.product.price for item in items),
            }
        return obj._totals_cache

    def get_total_count(self, obj):
        return self._totals(obj)["count"]

    def get_total_price(self, obj):
        return self._totals(obj)["price"]


class BasketProductAddSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в корзину."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN_VALUE,
        max_value=AMOUNT_MAX_VALUE,
        default=1,
    )


class BasketProductUpdateSerializer(serializers.Serializer):
    """Сериализатор для изменения количества товара в корзине."""

    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN_VALUE,
        max_value=AMOUNT_MAX_VALUE,
    )
