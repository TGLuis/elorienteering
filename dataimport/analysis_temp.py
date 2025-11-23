
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
            print(result.runner, end="\t")
        print("-"*12)