from django.urls import path

from .views import (
    CurrentUserView,
    DriverListView,
    RoleListView,
    UserDetailView,
    UserListCreateView,
)


urlpatterns = [
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current_user",
    ),
    path(
        "drivers/",
        DriverListView.as_view(),
        name="driver_list",
    ),
    path(
        "roles/",
        RoleListView.as_view(),
        name="role_list",
    ),
    path(
        "users/",
        UserListCreateView.as_view(),
        name="user_list_create",
    ),
    path(
        "users/<int:pk>/",
        UserDetailView.as_view(),
        name="user_detail",
    ),
]