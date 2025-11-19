import re
import os
import json
import requests
from datetime import datetime, time
import urllib.parse
from django.db import transaction, connection
from dateutil import tz

from django.db.models import QuerySet
from typing import Sequence


from dataimport.fetch_data import get_new_courses
from elo.models import Runner, Course, Ranking, Result


def get_courses_ids():
    for (dirpath, dirnames, filenames) in os.walk("dataimport/data/courses"):
        all_filenames = filenames
    all_courses = []
    for filename in all_filenames:
        try:
            with open(f"dataimport/data/courses/{filename}") as f:
                f.readline()
                date = datetime.fromisoformat(f.readline().split('"')[3])
                all_courses.append({"id": filename.split(".")[0], "date": date})
        except Exception as e:
            print(e)
            print(filename)
            exit()
    all_courses.sort(key=lambda x: x["date"])
    return [course["id"] for course in all_courses]

def get_helga_id(runner_name):
    response = requests.get(f"https://helga-o.com/webres/searchrunner.php?q={urllib.parse.quote(runner_name, safe='')}")
    if response.text == "" and "'" in runner_name:
        user_name_request = runner_name.replace("'", "&#39;")
        response = requests.get(f"https://helga-o.com/webres/searchrunner.php?q={urllib.parse.quote(user_name_request, safe='')}")
        return int(re.findall(r"runner=(\d+).*?>" + re.escape(user_name_request), response.text)[0])
    else:
        print(f"Requesting helga_id for runner: {runner_name}")
        return int(re.findall(r"runner=(\d+).*?>" + re.escape(runner_name), response.text)[0])

def get_runner_from_db(runner_name):
    try:
        return Runner.objects.get(fullname = runner_name)
    except Runner.DoesNotExist:
        runner = Runner(fullname=runner_name, helga_id=get_helga_id(runner_name))
        runner.save()
        return runner
    except Exception as e:
        if "get() returned more than one Runner" in str(e):
            Runner.objects.filter(fullname=runner_name)[1].delete()
            return get_runner_from_db(runner_name)
        print("Exception in get_runner_from_db")
        print(e)
        print(runner_name)
        exit()



def add_courses_json_to_db():
    get_new_courses()
    all_ids = get_courses_ids()
    for course_id in all_ids:
        with open(f"dataimport/data/courses/{course_id}.json") as f:
            print(course_id, end=", ", flush=True)
            if Course.objects.filter(helga_id=course_id).first() is not None:
                continue
            course_json = json.load(f)
            course = Course()
            course.helga_id = course_id
            course.name = course_json["name"]
            course.date = datetime.strptime(course_json["date"], "%Y-%m-%dT%H:%M:%S%z")
            course.location = course_json["location"]
            course.status = course_json["isLive"]

            results = []
            rankings = []
            for ranking_json in course_json["categories"].values():
                ranking = Ranking()
                ranking.course = course
                ranking.name = ranking_json["name"]
                ranking.distance = ranking_json["distance"]
                ranking.climb = ranking_json["climb"]
                rankings.append(ranking)

                for result_json in ranking_json["results"]:
                    if "VACANT" in result_json["name"] and (result_json["ageclass"] in [None, "-", ""] or (result_json["status"] != "OK" and result_json["time"] is None)):
                        continue
                    result = Result()
                    result.ranking = ranking
                    result.runner = get_runner_from_db(result_json["name"])
                    result.place = result_json["position"]
                    try:
                        result.time = time.fromisoformat(result_json["time"])
                    except:
                        result.time = None
                    result.status = result_json["status"]
                    result.date = course.date
                    results.append(result)

            with transaction.atomic():
                course.save()
                Ranking.objects.bulk_create(rankings)
                Result.objects.bulk_create(results)
    print("finished")


default_elo = 1500
def get_K(cur_result, n, number_of_previous_results):
    if number_of_previous_results < 5:
        k_base = 200
    elif number_of_previous_results < 10:
        k_base = 120
    elif number_of_previous_results < 30:
        k_base = 75
    else:
        k_base = 50
    if cur_result.runner.elo > 2000:
        k_base /= 2
    if n < 5:
        k_base /= 2
    elif n > 20:
        k_base *= (n / 20) ** 0.5
    return k_base / n


def get_mean_elo_others(valid_results: Sequence[Result], the_result: Result, previous_results, before: bool):
    if before and the_result.place == 1:
        return None
    elif not before and the_result.place == len(valid_results):
        return None
    mean_list = []
    current_place = the_result.place
    while len(mean_list) < 5:
        if before:
            current_place -= 1
            if current_place == 0:
                break
        else:
            current_place += 1
            if current_place > len(valid_results):
                break
        for valid_result in valid_results:
            if valid_result.place == current_place and previous_results[valid_result.pk] > 10:
                mean_list.append(float(valid_result.runner.elo))
                break
    if len(mean_list) == 0:
        return None
    if len(mean_list) > 1:
        mean_list.remove(max(mean_list))
    return rounded_mean(mean_list)

def rounded_mean(the_list: Sequence[float]):
    return round(sum(the_list)/len(the_list), 2)


def evaluate_first_elo(valid_results: Sequence[Result], the_result: Result, previous_results):
    elo_before = get_mean_elo_others(valid_results, the_result, previous_results, True)
    elo_after= get_mean_elo_others(valid_results, the_result, previous_results, False)
    if elo_before is None and elo_after is None:
        return the_result.runner.elo
    elo_mean = [] if previous_results[the_result.pk] == 0 else [float(the_result.runner.elo)]
    if elo_before is not None:
        elo_mean.append(elo_before)
    if elo_after is not None:
        elo_mean.append(elo_after)
    return rounded_mean(elo_mean)


@transaction.atomic
def compute_elo_diff(course, ranking):
    results = Result.objects.filter(ranking=ranking)
    handle_result_not_OK(results)

    valid_results = [result for result in results if result.place != 0]
    if len(valid_results) == 0:
        return
    if len(valid_results) == 1:
        valid_results[0].new_elo = valid_results[0].runner.elo
        valid_results[0].runner.active = True
        valid_results[0].save()
        valid_results[0].runner.save()
        return


    previous_results_pre_filter = Result.objects.filter(date__lt=course.date, status="OK")
    previous_results = {
        result.pk: previous_results_pre_filter.filter(runner=result.runner).count()
        for result in valid_results
    }

    for cur_result in valid_results:
        number_of_previous_results = previous_results[cur_result.pk]
        if number_of_previous_results < 3:
            new_elo = evaluate_first_elo(valid_results, cur_result, previous_results)
            cur_result.new_elo = new_elo
            cur_result.save()
            continue

        other_results = [result for result in valid_results if result != cur_result]
        # TODO startnumber is not in db !!
        #if concurrent.get("startnumber") is not None and len([1 for x in opponents if x["startnumber"] == concurrent["startnumber"]]) > 1:
        #    opponents = [x for x in concurrents if x["startnumber"] == concurrent["startnumber"]]
        n = len(other_results)
        if n < 1:
            cur_result.new_elo = cur_result.runner.elo
            continue

        K = get_K(cur_result, n, number_of_previous_results)

        elo_change = 0
        for other_result in other_results:
            opponent_previous_results = previous_results[other_result.pk]
            if number_of_previous_results < 10 and opponent_previous_results <= 10:
                #skip if you have more than 10 results but your opponent has less
                continue
            S = get_S(cur_result, other_result)
            # work out EA
            EA = 1 / (1.0 + 10.0 ** ((float(other_result.runner.elo) - float(cur_result.runner.elo)) / 400.0))
            # calculate ELO change vs this one opponent, add it to our change bucket
            elo_change += K * (S - EA)
        cur_result.new_elo = round(float(cur_result.runner.elo) + elo_change,2)
        cur_result.save()

    for result in valid_results:
        result.runner.elo = result.new_elo
        result.runner.active = True
        result.runner.save()


def get_S(cur_result: Result, other_result: Result) -> float:
    if cur_result.place == other_result.place:
        S = 0.5
    elif cur_result.place < other_result.place:
        S = 1.0
    else:
        S = 0.0
    return S


def handle_result_not_OK(results: QuerySet[Result, Result]):
    for result in results:
        if result.status == "NCL":
            result.new_elo = round(float(result.runner.elo) - 5.00, 2)
            result.runner.elo = result.new_elo
            result.runner.active = True
            result.save()
            result.runner.save()
        elif result.place == 0:
            result.new_elo = result.runner.elo
            result.runner.active = True
            result.save()
            result.runner.save()


def set_runner_inactive(last_year):
    beginning_of_last_year = datetime(last_year, 1, 1, 00, 00, 00, 0, tz.gettz("CET"))
    beginning_of_this_year = datetime(last_year+1, 1, 1, 00, 00, 00, 0, tz.gettz("CET"))
    with connection.cursor() as c:
        c.execute("UPDATE elo_runner SET active=0;")
        c.execute(f"""UPDATE elo_runner SET active=1 WHERE id IN (SELECT elo_runner.id FROM elo_runner JOIN elo_result ON elo_runner.id=elo_result.runner_id WHERE elo_result.date >= '{beginning_of_last_year.strftime("%Y-%m-%d")}' AND elo_result.date < '{beginning_of_this_year}');""")


def update_elo_runners_inactives(last_year):
    Runner.objects.raw("""UPDATE elo_runner SET elo_runner.elo = elo_runner.elo*0.99 WHERE elo_runner.active=0""")


def elo_for_courses():
    courses = Course.objects.order_by("date")
    year = 1900
    for course in courses:
        course_year = course.date.year
        if course_year > year:
            set_runner_inactive(year)
            update_elo_runners_inactives(year)
            year = course_year
        print(f"{course.helga_id}", end=", ", flush=True)
        rankings = Ranking.objects.filter(course=course)
        for ranking in rankings:
            compute_elo_diff(course, ranking)
    print()


@transaction.atomic
def update_dates_results():
    courses = Course.objects.all()
    for course in courses:
        Result.objects.filter(ranking__course=course).update(date=course.date)
