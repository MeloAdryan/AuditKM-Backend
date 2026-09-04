from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import (
    CurrentUserView,
    DriverListView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path(
        "api/auth/me/",
        CurrentUserView.as_view(),
        name="current_user",
    ),

    path(
        "api/auth/drivers/",
        DriverListView.as_view(),
        name="driver_list",
    ),

    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/",
        include("vehicles.urls"),
    ),

    path(
        "api/",
        include("trips.urls"),
    ),

    path(
        "api/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api-auth/",
        include("rest_framework.urls"),
    ),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )