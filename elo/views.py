from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template import loader

from .models import Runner, Result

def index(request):
    runners = Runner.objects.filter(active=True).order_by("-elo")
    template = loader.get_template("elo/index.html")
    the_runners = [{"elo": runner.elo, "place": x+1, "name": runner.fullname, "id": runner.pk} for x,runner in enumerate(runners)]
    context = {"runners" : the_runners}
    return HttpResponse(template.render(context, request))

def detail(request, runner_id):
    runner = get_object_or_404(Runner, pk=runner_id)
    template = loader.get_template("elo/runner.html")
    results = Result.objects.filter(runner=runner).order_by("-ranking__course__date")
    context = {"runner": runner, "results": results}
    return HttpResponse(template.render(context, request))

def about(request):
    template = loader.get_template("elo/about.html")
    return HttpResponse(template.render({}, request))

def page404():
    return HttpResponse("404 Not found !")

def runner_data(request, runner_id):
    results = Result.objects.filter(runner__pk=runner_id).order_by("date")
    #data = [{"date": result.ranking.course.date, "event": result.ranking.course.name, "rank": result.ranking.name, "status": result.status, "place": result.place, "elo": result.new_elo} for result in results]
    return JsonResponse({
        'labels': [result.ranking.course.date.timestamp() * 1000 for result in results],
        'elo': [float(result.new_elo) for result in results]
    })
