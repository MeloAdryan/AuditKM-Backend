from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    DashboardView,
    StandardRoutePointViewSet,
    StandardRouteViewSet,
    TripViewSet,
)


router = DefaultRouter()

router.register(
    r"trips",
    TripViewSet,
    basename="trip",
)

router.register(
    r"standard-routes",
    StandardRouteViewSet,
    basename="standard-route",
)

router.register(
    r"standard-route-points",
    StandardRoutePointViewSet,
    basename="standard-route-point",
)


urlpatterns = [
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
]

urlpatterns += router.urls