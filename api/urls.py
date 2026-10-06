from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from .views import BasketViewSet, CategoryViewSet, ProductViewSet

app_name = "api"

schema_view = get_schema_view(
    openapi.Info(
        title="API проекта",
        default_version="v1",
        description="Документация для API проекта",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router_v1 = DefaultRouter()
router_v1.register("categories", CategoryViewSet, basename="categories")
router_v1.register("products", ProductViewSet, basename="products")
router_v1.register("basket", BasketViewSet, basename="basket")


urlpatterns = [
    path("", include(router_v1.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]
