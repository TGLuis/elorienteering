from math import floor
from django.core.cache import cache
from django.db.models import Count, Max, Min

from elo.models import Result, Runner, Affiliation


def get_restless_from_cache(active_year):
    if active_year == "year":
        return cache.get_or_set(
            "restless_year",
            lambda: (Result.objects.filter(status="OK").values("source__runner__fullname", "source__runner__pk",
                                                               "source__runner__nationality")
                     .annotate(count=Count("source__runner")).filter(count__gte=3).order_by("-count")),
            timeout=14400  # 4 hours
        )
    return cache.get_or_set(
        f"restless_year-{active_year}",
        lambda: (Result.objects.filter(status="OK", date__gte=f"{active_year}-01-01 00:00+01:00",
                                       date__lt=f"{int(active_year) + 1}-01-01 00:00+01:00")
                 .values("source__runner__fullname", "source__runner__pk", "source__runner__nationality")
                 .annotate(count=Count("source__runner")).filter(count__gte=3).order_by("-count")),
        timeout=14400  # 4 hours
    )


def get_main_ranking_from_cache():
    return cache.get_or_set(
        "main_ranking",
        lambda: Runner.objects.filter(active=True, number_of_valid_courses__gte=3).order_by("-elo"),
        timeout=14400  # 4 hours
    )


def get_all_affiliations_from_cache():
    return cache.get_or_set(
        "all_affiliations",
        Affiliation.objects.all,
        timeout=14400  # 4 hours
    )


def get_all_categories_from_cache():
    return cache.get_or_set(
        "categories",
        lambda: list(Runner.objects.exclude(category="").values_list("category", flat=True).distinct()),
        timeout=2592000  # 30 days
    )


def get_all_clubs_from_cache():
    return cache.get_or_set(
        "clubs", lambda: list(Affiliation.objects.exclude(club="").values_list("club", flat=True).distinct()),
        timeout=2592000  # 30 days
    )


def get_all_affiliation_countries_from_cache():
    return cache.get_or_set(
        "affiliation_countries",
        lambda: list(Affiliation.objects.exclude(country="").values_list("country", flat=True).distinct()),
        timeout=2592000  # 30 days
    )


def _elo_data():
    interval = 100
    labels, values = [], []
    min_elo = float(Runner.objects.filter(number_of_valid_courses__gt=3, active=True).aggregate(Min("elo"))["elo__min"])
    max_elo = float(Runner.objects.filter(number_of_valid_courses__gt=3, active=True).aggregate(Max("elo"))["elo__max"])
    runner_with_more_than_3_results = Runner.objects.filter(number_of_valid_courses__gt=3, active=True)
    total_runners = runner_with_more_than_3_results.count()
    min_elo = floor(min_elo / interval) * interval
    max_elo = floor(max_elo / interval) * interval
    for elo in range(min_elo, max_elo + 1, interval):
        runners_with_elo = runner_with_more_than_3_results.filter(elo__gte=elo, elo__lt=elo + interval).count()
        labels.append(elo)
        values.append(round((runners_with_elo / total_runners) * 100, 2))
    return labels, values


def get_elo_data():
    return cache.get_or_set(
        "elo_distribution", _elo_data,
        timeout=86400  # 24 hours
    )


def _elo_update_data():
    all_results, labels, values = [], [], []

    runner_with_more_than_30_results = (Result.objects.filter(status="OK").values("source__runner__pk").
                                        annotate(count=Count("source__runner")).order_by("-count").filter(
        count__gte=31).
                                        values_list("source__runner__pk", flat=True))
    for runner_id in runner_with_more_than_30_results:
        all_results.extend(Result.objects.filter(status="OK", source__runner=runner_id).exclude(place=0).
                           exclude(elo_diff=0.00).order_by("date")[31:].
                           values_list("elo_diff", flat=True))
    all_results = list(map(lambda x: round(float(x)), all_results))
    min_elo_update = min(all_results)
    max_elo_update = max(all_results)
    for elo in range(min_elo_update, max_elo_update + 1):
        labels.append(elo)
        values.append(round(all_results.count(elo) / len(all_results), 4))
    return labels, values


def get_elo_update_data():
    return cache.get_or_set(
        "elo_diff", _elo_update_data,
        timeout=86400  # 24 hours
    )
