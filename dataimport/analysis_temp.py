import logging

import matplotlib.pyplot as plt
import numpy as np
from django.db.models import Max, Min, Count

from elo.models import Runner, Course, Ranking, Result


logger = logging.getLogger(__name__)


def display_course_elo_change(helga_id):
    course = Course.objects.get(source_id=helga_id)
    rankings = Ranking.objects.filter(course__source_id=helga_id)
    logger.info(course)
    logger.info("="*20)
    for ranking in rankings:
        logger.info("-"*12)
        logger.info(ranking)
        results = Result.objects.filter(ranking=ranking).order_by("place")
        for result in results:
            logger.info(result, end="\t")
            logger.info(result.runner)
        logger.info("-"*12)

def display_ncl_percentage_per_elo():
    min_elo = float(Result.objects.all().aggregate(Min("new_elo"))["new_elo__min"])
    max_elo = float(Result.objects.all().aggregate(Max("new_elo"))["new_elo__max"])
    for i in range(int(min_elo//100), int(max_elo // 100 + 1)):
        logger.info(f"{i * 100} - {(i + 1) * 100}: ",
              100 *
              len(Result.objects.filter(new_elo__gte=i * 100, new_elo__lt=(i + 1) * 100, status="NCL")) /
              len(Result.objects.filter(new_elo__gte=i * 100, new_elo__lt=(i + 1) * 100))
        )

def display_ncl_percentage_per_runner(name):
    runner = Runner.objects.filter(fullname=name)[0]
    logger.info(f"{name} NCL percentage: ",
          100 *
          len(Result.objects.filter(runner=runner, status="NCL")) /
          len(Result.objects.filter(runner=runner))
    )

def distribution_of_elo_update():
    runner_with_more_than_30_results = Result.objects.filter(status="OK").values("runner__fullname", "runner__pk").annotate(count=Count("runner")).order_by("-count").filter(count__gte=31)
    results = []
    for runner in runner_with_more_than_30_results:
        results.extend(list(Result.objects.filter(status="OK",runner__pk=runner['runner__pk']).exclude(place=0).exclude(elo_diff=0.00).order_by("date")[31:]))
    elo_diff_array = np.array([float(res.elo_diff) for res in results])
    # Calculate basic statistics
    logger.info(f"Mean: {np.mean(elo_diff_array):.2f}")
    logger.info(f"Standard Deviation: {np.std(elo_diff_array):.2f}")
    plt.hist(elo_diff_array, bins=300, density=True)
    plt.title("elo diff Distribution", fontsize=18)
    plt.xlabel("Value", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)
    plt.show()
    return elo_diff_array

def distribution_of_elo():
    runner_with_more_than_3_results = Runner.objects.filter(number_of_valid_courses__gt=3)
    elo_array = np.array([float(runner.elo) for runner in runner_with_more_than_3_results])
    # Calculate basic statistics
    logger.info(f"Mean: {np.mean(elo_array):.2f}")
    logger.info(f"Standard Deviation: {np.std(elo_array):.2f}")
    plt.hist(elo_array, bins=100, density=True)
    plt.title("elo Distribution", fontsize=18)
    plt.xlabel("Value", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)
    plt.show()
    return elo_array

