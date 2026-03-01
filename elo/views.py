from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.template import loader
from django.core.paginator import Paginator
from itertools import zip_longest

from .utils import Navigation
from .models import Runner, Result

def index(request):
    runners = Runner.objects.filter(active=True, number_of_valid_courses__gte=3).order_by("-elo")
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
    results = Result.objects.filter(runner=runner).order_by("-ranking__course__date")
    context = {"runner": runner, "results": results}
    return HttpResponse(template.render(context, request))

def categories(request):
    template = loader.get_template("elo/categories.html")
    categories = list(Runner.objects.all().values_list("category", flat=True).distinct())
    dames = [category for category in categories if category and category[0] == "D"]
    hommes = [category for category in categories if category and category[0] == "H"]
    categories = [{"man": homme, "woman": dame} for homme,dame in zip_longest(hommes, dames, fillvalue="")]
    return HttpResponse(template.render({"categories": categories}, request))

def category(request, category_name):
    categories = list(Runner.objects.all().values_list("category", flat=True).distinct())
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
    context = {"runners" : the_runners, "nav": nav, "base": f"belgium/", "params": f"&fede={fede}", "title": f"Belgian Ranking{ '' if (fede not in fedes) else (' - ' + fede)}"}
    return HttpResponse(template.render(context, request))


def about(request):
    template = loader.get_template("elo/about.html")
    return HttpResponse(template.render({}, request))

def runner_data(request, runner_id):
    results = Result.objects.filter(runner__pk=runner_id).order_by("date")
    return JsonResponse({
        'dataset': [[result.ranking.course.date.timestamp() * 1000, float(result.new_elo)] for result in results],
    })

def runner_search(request):
    runners = Runner.objects.filter(fullname__icontains=request.GET['runner_pattern'])[:10]
    return JsonResponse([{"name":runner.fullname,"url":f"/elo/{runner.helga_id}"} for runner in runners], safe=False)

def runner_compare(request):
    runners = Runner.objects.filter(fullname__icontains=request.GET['runner_pattern'])[:10]
    return JsonResponse([{"name":runner.fullname,"id":runner.pk} for runner in runners], safe=False)

