from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # API v1
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/shops/", include("apps.shops.urls")),
    path("api/v1/products/", include("apps.products.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/wallet/", include("apps.wallet.urls")),
    path("api/v1/udhaar/", include("apps.udhaar.urls")),
    path("api/v1/emi/", include("apps.emi.urls")),
    path("api/v1/delivery/", include("apps.delivery.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/coupons/", include("apps.coupons.urls")),
    path("api/v1/support/", include("apps.support.urls")),
    path("api/v1/iot/", include("apps.iot.urls")),
    path("api/v1/gis/", include("apps.gis.urls")),
    path("api/v1/videos/", include("apps.videos.urls")),
    path("api/v1/whatsapp/", include("apps.whatsapp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
