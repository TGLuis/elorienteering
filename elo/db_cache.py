from django.core.cache import cache
from django.db.models import Count

from elo.models import Result, Runner


def get_restless_from_cache(active_year):
    if active_year == "year":
        return cache.get_or_set(
            "restless_year",
            (Result.objects.filter(status="OK").values("runner__fullname", "runner__pk")
             .annotate(count=Count("runner")).filter(count__gte=3).order_by("-count")),
            timeout=14400  # 4 hours
        )
    return cache.get_or_set(
        f"restless_year-{active_year}",
        (Result.objects.filter(status="OK", date__gte=f"{active_year}-01-01 00:00+01:00",
                               date__lt=f"{int(active_year) + 1}-01-01 00:00+01:00")
         .values("runner__fullname", "runner__pk")
         .annotate(count=Count("runner")).filter(count__gte=3).order_by("-count")),
        timeout=14400  # 4 hours
    )


def get_main_ranking_from_cache():
    return cache.get_or_set(
        "main_ranking",
        Runner.objects.filter(active=True, number_of_valid_courses__gte=3).order_by("-elo"),
        timeout=14400  # 4 hours
    )

def get_all_categories_from_cache():
    return cache.get_or_set(
        "categories",
        list(Runner.objects.exclude(category="").values_list("category", flat=True).distinct()),
        timeout=2592000  # 30 days
    )

def get_all_clubs_from_cache():
    return cache.get_or_set(
        "clubs",list(Runner.objects.exclude(club="").values_list("club", flat=True).distinct()),
        timeout=2592000  # 30 days
    )
