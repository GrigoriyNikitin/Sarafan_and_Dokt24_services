from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from products.models import Basket, BasketProduct, Category, Product

from .constants import AMOUNT_MAX_VALUE
from .pagination import PageLimitPagination
from .serializers import (
    BasketProductAddSerializer,
    BasketProductSerializer,
    BasketProductUpdateSerializer,
    BasketSerializer,
    CategorySerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра категорий и подгатегорий."""

    queryset = Category.objects.prefetch_related("subcategories").all()
    serializer_class = CategorySerializer
    pagination_class = PageLimitPagination
    permission_classes = (AllowAny,)
    lookup_field = "slug"


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра продуктов."""

    queryset = Product.objects.select_related("subcategory", "subcategory__category")
    serializer_class = ProductSerializer
    pagination_class = PageLimitPagination
    permission_classes = (AllowAny,)
    lookup_field = "slug"


class BasketViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ViewSet для просмотра и редактирования корзины текущего пользователя."""

    serializer_class = BasketSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Basket.objects.filter(user=self.request.user).prefetch_related(
            "basket_items__product"
        )

    def _get_basket(self) -> Basket:
        """
        Гарантированно возвращает корзину
        пользователя (создаёт при отсутствии).
        """
        basket, _ = Basket.objects.get_or_create(user=self.request.user)
        return basket

    @action(detail=False, methods=("delete",), url_path="clear")
    def clear(self, request):
        """Полная очистка корзины текущего пользователя."""
        basket = self.get_queryset().first()
        if basket is None:
            return Response(
                {"detail": "Корзина пуста."},
                status=status.HTTP_204_NO_CONTENT,
            )

        deleted, _ = BasketProduct.objects.filter(basket=basket).delete()
        return Response(
            {"deleted": deleted},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=("post",), url_path="products")
    def add_product(self, request):
        """Добавление продукта в корзину."""
        serializer = BasketProductAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        basket = self._get_basket()
        product = serializer.validated_data["product"]
        amount = serializer.validated_data["amount"]

        item, created = BasketProduct.objects.get_or_create(
            basket=basket,
            product=product,
            defaults={"amount": amount},
        )

        if not created:
            new_amount = item.amount + amount
            if new_amount > AMOUNT_MAX_VALUE:
                raise ValidationError({"amount": f"Максимум {AMOUNT_MAX_VALUE} шт."})
            item.amount = new_amount
            item.save(update_fields=("amount",))

        return Response(
            BasketProductSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=("patch", "delete"),
        url_path=r"products/(?P<product_slug>[-a-zA-Z0-9_]+)",
    )
    def manage_product(self, request, product_slug=None):
        """Удаление продукта из корзины или изменение его количества."""
        basket = self._get_basket()
        item = get_object_or_404(
            BasketProduct,
            basket=basket,
            product__slug=product_slug,
        )

        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PATCH — устанавливаем точное количество
        serializer = BasketProductUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item.amount = serializer.validated_data["amount"]
        item.save(update_fields=("amount",))

        return Response(BasketProductSerializer(item).data)
