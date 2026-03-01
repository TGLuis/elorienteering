import datetime

from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.template import loader
from django.core.paginator import Paginator
from itertools import zip_longest

from .db_cache import get_restless_from_cache, get_main_ranking_from_cache, get_all_categories_from_cache
from .utils import Navigation
from .models import Runner, Result


def index(request):
    runners = get_main_ranking_from_cache()
    pages = Paginator(runners, 100)
    page_number = int(request.GET.get("page", "1"))
    nav = Navigation(pages, page_number)
    current_page = pages.page(page_number)
    template = loader.get_template("elo/index.html")
    the_runners = [{"properties": runner, "place": x} for x,runner in zip(range(current_page.start_index(), current_page.end_index()+1), current_page)]
    context = {"runners" : the_runners, "nav": nav}
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
    runner = get_object_or_404(Runner, helga_id=runner_id)
    template = loader.get_template("elo/runner.html")
    results = Result.objects.filter(runner=runner).order_by("-date")
    total_delta = [datetime.timedelta(hours=result.time.hour,minutes=result.time.minute,seconds=result.time.second).total_seconds() for result in results if result.time is not None]
    context = {
        "runner": runner,
        "results": results,
        "number_of_results": len(results.exclude(status="DNS")),
        "pm_percentage": round(100*len(results.filter(status="NCL"))/len(results.exclude(status="DNS")), 2),
        "highest_elo": max(results[:len(results)-30], key=lambda x: x.new_elo).new_elo if len(results) > 30 else "-",
        "total_time": datetime.timedelta(seconds=sum(total_delta))
    }
    return HttpResponse(template.render(context, request))


def get_categories(request):
    template = loader.get_template("elo/categories.html")
    categories = get_all_categories_from_cache()
    dames = [category for category in categories if category and category[0] == "D"]
    hommes = [category for category in categories if category and category[0] == "H"]
    categories = [{"man": homme, "woman": dame} for homme,dame in zip_longest(hommes, dames, fillvalue="")]
    return HttpResponse(template.render({"categories": categories}, request))


def get_category(request, category_name):
    categories = get_all_categories_from_cache()
    if category_name not in categories:
        raise Http404("Ranking does not exist")
    template = loader.get_template("elo/category.html")
    runners = Runner.objects.filter(category=category_name, number_of_valid_courses__gte=3).order_by("-elo")
    pages = Paginator(runners, 100)
    page_number = int(request.GET.get("page", "1"))
    nav = Navigation(pages, page_number)
    current_page = pages.page(page_number)
    the_runners = [{"properties": runner, "place": x} for x,runner in zip(range(current_page.start_index(), current_page.end_index()+1), current_page)]
    context = {"runners" : the_runners, "nav": nav, "base": f"category/{category_name}/", "category_name": category_name, "title": f"Belgian Ranking - {category_name}"}
    return HttpResponse(template.render(context, request))

def belgium(request):
    fede = request.GET.get("fede", "-")
    runners = Runner.objects.filter(abso=True, number_of_valid_courses__gte=3)
    fedes = ["FRSO", "OV"]
    if fede in fedes:
        runners = runners.filter(fede=fede)
    runners = runners.order_by("-elo")
    template = loader.get_template("elo/category.html")
    pages = Paginator(runners, 100)
    page_number = int(request.GET.get("page", "1"))
    nav = Navigation(pages, page_number)
    current_page = pages.page(page_number)
    the_runners = [{"properties": runner, "place": x} for x,runner in zip(range(current_page.start_index(), current_page.end_index()+1), current_page)]
    context = {"runners" : the_runners, "nav": nav, "base": f"belgium/", "other_params": f"&fede={fede}", "title": f"Belgian Ranking{ '' if (fede not in fedes) else (' - ' + fede)}"}
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
    the_runners = [{"name": runner["runner__fullname"], "helga_id": runner["runner__helga_id"], "count": runner["count"], "place": x}
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
    return JsonResponse([{"name":runner.fullname,"url":f"/elo/{runner.helga_id}"} for runner in runners], safe=False)


def runner_compare(request):
    runners = Runner.objects.filter(fullname__icontains=request.GET['runner_pattern'])[:10]
    return JsonResponse([{"name":runner.fullname,"id":runner.pk} for runner in runners], safe=False)

