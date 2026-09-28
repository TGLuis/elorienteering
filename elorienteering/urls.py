"""
URL configuration for elorienteering project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from elo.models import Runner, Course, Result
from elo.db_cache import get_all_affiliations_from_cache

class RunnerSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.1

    def items(self):
        affiliations = get_all_affiliations_from_cache()
        return Runner.objects.filter(active=True, number_of_valid_courses__gte=3).filter(
            pk__in=affiliations.values_list("runner")).order_by("-elo")

    def location(self, runner):
        return reverse("runner") + f"?id={runner.pk}"

    def lastmod(self, runner):
        return Result.objects.filter(source__runner=runner).order_by("-date").first().date

class CourseSitemap(Sitemap):
    changefreq = "never"
    priority = 0.1

    def items(self):
        return Course.objects.order_by("-date")[:100]

    def location(self, course):
        return reverse("course") + f"?id={course.pk}"

    def lastmod(self, course):
        return course.date

class RankingsSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def items(self):
        return ["index", "restless", "courses"]

    def location(self, item):
        return reverse(item)


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ["compare", "about"]

    def location(self, item):
        return reverse(item)

urlpatterns = [
    path("", RedirectView.as_view(url="/elo/"), name="root"),
    path("elo/", include("elo.urls")),
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": {
        "static": StaticViewSitemap,
        "rankings": RankingsSitemap,
        "courses": CourseSitemap,
        "runners": RunnerSitemap,
    }}, name="django.contrib.sitemaps.views.sitemap"),
]