import datetime

from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.template import loader
from django.core.paginator import Paginator

from .db_cache import get_restless_from_cache, get_main_ranking_from_cache, get_all_categories_from_cache, get_all_clubs_from_cache
from .utils import Navigation
from .models import Runner, Result


def handle_filters(request):
    params = {"countries": [], "sex": [], "age": [], "clubs": []}
    other_params = []
    countries = request.GET.get("countries")
    if countries is not None:
        params["countries"] = countries.split(",")
        other_params.append("countries="+countries)
    sex = request.GET.get("sex")
    if sex is not None:
        params["sex"] = sex.split(",")
        other_params.append("sex="+sex)
    age = request.GET.get("age")
    if age is not None:
        params["age"] = age.split(",")
        other_params.append("age="+age)
    clubs = request.GET.get("clubs")
    if clubs is not None:
        params["clubs"] = clubs.split(",")
        other_params.append("clubs="+clubs)
    return params, "&".join(other_params)

def apply_filters(runners, filters):
    if filters.get("countries"):
        if filters.get("countries")[0] == "BEL":
            runners = runners.filter(abso=True)
    if filters.get("sex") and len(filters.get("sex")) == 1:
        if filters.get("sex")[0] == "W":
            runners = runners.filter(sex="F")
        else:
            runners = runners.filter(sex="M")
    if filters.get("age"):
        age_categories = ["D"+age for age in filters.get("age")] + ["H"+age for age in filters.get("age")]
        runners = runners.filter(category__in=age_categories)
    if filters.get("clubs"):
        runners = runners.filter(club__in=filters.get("clubs"))
    return runners

def set_all_filters(filters_selected):
    categories = get_all_categories_from_cache()
    age_categories = sorted({category[1:] for category in categories})
    clubs = get_all_clubs_from_cache()
    all_filters = {
        "countries": {"BEL": "BEL" in filters_selected["countries"]},
        "sex": {"M": "M" in filters_selected["sex"], "W": "W" in filters_selected["sex"]},
        "age": {age: age in filters_selected["age"] for age in age_categories},
        "clubs": {club: club in filters_selected["clubs"] for club in clubs}
    }
    return all_filters


def index(request):
    filters_selected, other_params = handle_filters(request)
    runners = apply_filters(get_main_ranking_from_cache(), filters_selected)
    pages = Paginator(runners, 100)
    page_number = int(request.GET.get("page", "1"))
    nav = Navigation(pages, page_number)
    current_page = pages.page(page_number)
    template = loader.get_template("elo/index.html")
    the_runners = [{"properties": runner, "place": x} for x,runner in zip(range(current_page.start_index(), current_page.end_index()+1), current_page)]
    all_filters = set_all_filters(filters_selected)
    context = {
        "runners" : the_runners,
        "nav": nav,
        "all_filters": all_filters,
        "other_params": "&"+other_params,
        "badges": other_params.split("&")
    }
    return HttpResponse(template.render(context, request))


def compare(request):
    template = loader.get_template("elo/compare.html")
    return HttpResponse(template.render({}, request))


def ranking(request, ranking_id):
    results = Result.objects.filter(ranking__pk=ranking_id)
    if not results:
        raise Http404("Ranking does not exist")
    template = loader.get_template("elo/ranking.html")
    return HttpResponse(template.render({"results": results, "ranking": results.first().ranking}, request))


def detail(request, runner_id):
    runner = get_object_or_404(Runner, pk=runner_id)
    template = loader.get_template("elo/runner.html")
    results = Result.objects.filter(runner=runner).order_by("-date")
    total_delta = [datetime.timedelta(hours=result.time.hour,minutes=result.time.minute,seconds=result.time.second).total_seconds() for result in results if result.time is not None]
    context = {
        "runner": runner,
        "results": results,
        "number_of_results": len(results.exclude(status="DNS")),
        "pm_percentage": round(100*len(results.filter(status="NCL"))/len(results.exclude(status="DNS")), 2) if len(results.exclude(status="DNS")) > 0 else "Not applicable",
        "highest_elo": max(results[:len(results)-30], key=lambda x: x.new_elo).new_elo if len(results) > 30 else "-",
        "total_time": datetime.timedelta(seconds=sum(total_delta))
    }
    return HttpResponse(template.render(context, request))


def restless(request):
    years = list(range(2005,datetime.date.today().year+1))
    if (active_year := request.GET.get("year", "year")) != "year":
        if int(active_year) not in years:
            raise Http404(f"Year {request.GET.get('year')} does not have any result")
    template = loader.get_template("elo/restless.html")
    runners = get_restless_from_cache(active_year)
    pages = Paginator(runners, 100)
    page_number = int(request.GET.get("page", "1"))
    nav = Navigation(pages, page_number)
    current_page = pages.page(page_number)
    the_runners = [{"name": runner["runner__fullname"], "pk": runner["runner__pk"], "count": runner["count"], "place": x}
    for x,runner in zip(range(current_page.start_index(), current_page.end_index()+1), current_page)]
    context = {"runners" : the_runners, "nav": nav, "base": f"restless/", "years": years[::-1], "active_year":active_year, "other_params":f"&year={active_year}"}
    return HttpResponse(template.render(context, request))


def about(request):
    template = loader.get_template("elo/about.html")
    return HttpResponse(template.render({}, request))


def runner_data(request, runner_id):
    results = Result.objects.filter(runner__pk=runner_id).order_by("date")
    return JsonResponse({'dataset': [[result.date.timestamp() * 1000, float(result.new_elo)] for result in results]})


def runner_search(request):
    runners = Runner.objects.filter(fullname__icontains=request.GET['runner_pattern'])[:10]
    return JsonResponse([{"name":runner.fullname,"url":f"/elo/runner/{runner.pk}"} for runner in runners], safe=False)


def runner_compare(request):
    runners = Runner.objects.filter(fullname__icontains=request.GET['runner_pattern'])[:10]
    return JsonResponse([{"name":runner.fullname,"id":runner.pk} for runner in runners], safe=False)

