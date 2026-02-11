from django.urls import path

from elo import views

urlpatterns = [
    path("", views.index, name="index"),
    path("compare", views.compare, name="compare"),
    path("ranking/<int:ranking_id>/", views.ranking, name="ranking"),
    path("restless/", views.restless, name="restless"),
    path("categories", views.get_categories, name="categories"),
    path("category/<str:category_name>/", views.get_category, name="category"),
    path("about", views.about, name="about"),
    path("<int:runner_id>/", views.detail, name="runner"),
    path("api/runner/<int:runner_id>/", views.runner_data, name="runner_data"),
    path("api/runner/search", views.runner_search , name="runner_search"),
    path("api/runner/compare", views.runner_compare, name="runner_compare"),
]