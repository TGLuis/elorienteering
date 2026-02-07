from django.db.models import Max, Min

from elo.models import Runner, Course, Ranking, Result

def display_course_elo_change(helga_id):
    course = Course.objects.get(helga_id=helga_id)
    rankings = Ranking.objects.filter(course__helga_id=helga_id)
    print(course)
    print("="*20)
    for ranking in rankings:
        print("-"*12)
        print(ranking)
        results = Result.objects.filter(ranking=ranking).order_by("place")
        for result in results:
            print(result, end="\t")
            print(result.runner)
        print("-"*12)

def display_ncl_percentage_per_elo():
    min = float(Result.objects.all().aggregate(Min("new_elo"))["new_elo__min"])
    max = float(Result.objects.all().aggregate(Max("new_elo"))["new_elo__max"])
    for i in range(int(min//100), int((max)//100+1)):
        print(f"{i * 100} - {(i + 1) * 100}: ",
              100 *
              len(Result.objects.filter(new_elo__gte=i * 100, new_elo__lt=(i + 1) * 100, status="NCL")) /
              len(Result.objects.filter(new_elo__gte=i * 100, new_elo__lt=(i + 1) * 100))
        )

def display_ncl_percentage_per_runner(name):
    runner = Runner.objects.filter(fullname=name)[0]
    print(f"{name} NCL percentage: ",
          100 *
          len(Result.objects.filter(runner=runner, status="NCL")) /
          len(Result.objects.filter(runner=runner))
    )