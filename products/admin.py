from django.contrib import admin

from .models import Basket, BasketProduct, Category, Product, SubCategory


@admin.register(BasketProduct)
class BasketProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "subcategories_list")

    @admin.display(description="Подкатегории")
    def subcategories_list(self, obj):
        return ", ".join(obj.subcategories.values_list("name", flat=True)) or "—"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "subcategory", "price")


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    pass


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
