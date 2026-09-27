from django.urls import path

from elo import views

urlpatterns = [
    path("", views.index, name="index"),
    path("compare", views.compare, name="compare"),
    path("ranking", views.ranking, name="ranking"),
    path("course", views.course, name="course"),
    path("future", views.future, name="future"),
    path("courses", views.courses, name="courses"),
    path("restless", views.restless, name="restless"),
    path("about", views.about, name="about"),
    path("runner", views.detail, name="runner"),
    path("api/runner", views.runner_data, name="runner_data"),
    path("api/runner/search", views.runner_search , name="runner_search"),
    path("api/runner/compare", views.runner_compare, name="runner_compare"),
]