from django.urls import path

from elo import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:runner_id>/", views.detail, name="runner"),
    path("api/<int:runner_id>/", views.runner_data, name="runner_data")
]