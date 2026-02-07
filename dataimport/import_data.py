import os 
import json
from datetime import datetime, time
from django.db import transaction, connection
from dateutil import tz

from django.db.models import QuerySet
from typing import Sequence


from dataimport.fetch_data import get_new_courses, get_courses_ids, get_helga_id, is_vacant_result
from elo.models import Runner, Course, Ranking, Result

DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))


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
        with open(f"{DIR_PATH}/data/courses/{course_id}.json") as f:
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
            course.save()

            results = []
            for ranking_json in course_json["categories"].values():
                ranking = Ranking()
                ranking.course = course
                ranking.name = ranking_json["name"]
                ranking.distance = ranking_json["distance"]
                ranking.climb = ranking_json["climb"]
                ranking.save()

                for result_json in ranking_json["results"]:
                    if is_vacant_result(result_json):
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
                    result.startnumber = result_json.get("startnumber", 0)
                    results.append(result)

            Result.objects.bulk_create(results)
    print("finished")



default_elo = 1600
def get_k_base(cur_result, n, number_of_previous_results):
    # ! k_base should be divided by the number of updates !
    if number_of_previous_results < 5:
        k_base = 200
    elif number_of_previous_results < 10:
        k_base = 120
    elif number_of_previous_results < 30:
        k_base = 75
    else:
        k_base = 50
    if n < 5:
        k_base /= 2
    elif n > 20:
        k_base *= (n / 20) ** 0.5
    return k_base


def get_mean_elo_others(valid_results: Sequence[Result], the_result: Result, before: bool):
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
            if valid_result.place == current_place and valid_result.runner.number_of_valid_courses > 3:
                mean_list.append(float(valid_result.runner.elo))
    if len(mean_list) < 2:
        return None
    mean_list.remove(max(mean_list))
    return rounded_mean(mean_list)

def rounded_mean(the_list: Sequence[float]):
    return round(sum(the_list)/len(the_list), 2)


def evaluate_first_elo(valid_results: Sequence[Result], the_result: Result):
    elo_before = get_mean_elo_others(valid_results, the_result, True)
    elo_after= get_mean_elo_others(valid_results, the_result, False)
    if elo_before is None and elo_after is None:
        return the_result.runner.elo
    elo_mean = [] if the_result.runner.number_of_valid_courses == 0 else [float(the_result.runner.elo)]
    if elo_before is not None:
        elo_mean.append(max(min(elo_before, 2000), 1000))
    if elo_after is not None:
        elo_mean.append(min(max(elo_after, 1000), 2000))
    return rounded_mean(elo_mean)

def get_real_opponents(number_of_previous_results, valid_results, cur_result):
    other_results = {result.place:result for result in valid_results if result != cur_result}
    if cur_result.startnumber != 0 and len([1 for x in other_results.values() if x.startnumber == cur_result.startnumber]):
        other_results = {x.place:x for x in other_results.values() if x.startnumber == cur_result.startnumber}

    real_opponents = []
    places = sorted(other_results.keys())
    found_before = found_after = 0
    for i in [place for place in places if place < cur_result.place][::-1]:
        # skip if you have more than 10 results but your opponent has less
        if number_of_previous_results < 11 or 11 < other_results[i].runner.number_of_valid_courses:
            found_before += 1
            real_opponents.append(other_results[i])
            if found_before == 10:
                break
    for i in [place for place in places if place > cur_result.place]:
        # skip if you have more than 10 results but your opponent has less
        if number_of_previous_results < 11 or 11 < other_results[i].runner.number_of_valid_courses:
            found_after += 1
            real_opponents.append(other_results[i])
            if found_after == 10:
                break

    return real_opponents


@transaction.atomic
def compute_elo_diff(ranking):
    results = Result.objects.filter(ranking=ranking)
    handle_result_not_OK(results)

    valid_results = [result for result in results if result.place != 0]
    if len(valid_results) == 0:
        return
    if len(valid_results) == 1:
        only_one_runner(valid_results[0])
        return


    for cur_result in valid_results:
        number_of_previous_results = cur_result.runner.number_of_valid_courses
        if number_of_previous_results < 3:
            first_three_results(cur_result, valid_results)
            continue

        other_results = get_real_opponents(number_of_previous_results, valid_results, cur_result)
        n = len(other_results)
        if n < 1:
            only_one_runner(cur_result)
            continue

        k_base = get_k_base(cur_result, n, number_of_previous_results)

        elo_change = get_elo_change(cur_result, k_base, other_results)
        save_elo_change(cur_result, elo_change)
    save_all_runners(valid_results)


def save_elo_change(cur_result, elo_change):
    if cur_result.runner.elo < 600 and elo_change < 0:
        elo_change /= 2
    cur_result.elo_diff = round(elo_change, 2)
    cur_result.new_elo = round(float(cur_result.runner.elo) + elo_change, 2)
    cur_result.save()


def save_all_runners(valid_results):
    for result in valid_results:
        result.runner.elo = result.new_elo
        result.runner.number_of_valid_courses += 1
        result.runner.active = True
        result.runner.save()


def get_elo_change(cur_result, k_base, other_results):
    elo_change = 0
    real_n = 0  # number of people really participating in the update of the elo.
    for other_result in other_results:
        real_n += 1
        S = get_S(cur_result, other_result)
        # work out EA
        EA = 1 / (1.0 + 10.0 ** ((float(other_result.runner.elo) - float(cur_result.runner.elo)) / 400.0))
        # calculate ELO change vs this one opponent, add it to our change bucket
        elo_change += S - EA
    if real_n > 0:
        elo_change *= k_base / real_n
    return elo_change


def first_three_results(cur_result, valid_results):
    new_elo = evaluate_first_elo(valid_results, cur_result)
    cur_result.new_elo = new_elo
    cur_result.elo_diff = 0
    cur_result.save()


def only_one_runner(result):
    result.new_elo = result.runner.elo
    result.elo_diff = 0
    result.runner.active = True
    result.save()
    result.runner.save()


def get_S(cur_result: Result, other_result: Result) -> float:
    if cur_result.place == other_result.place:
        return 0.5
    elif cur_result.place < other_result.place:
        return 1.0
    else:
        return 0.0


def handle_result_not_OK(results: QuerySet[Result, Result]):
    for result in results:
        if result.status == "NCL":
            result.elo_diff = -round(float(result.runner.elo)*0.005, 2)
            result.new_elo = round(float(result.runner.elo) + float(result.elo_diff), 2)
            result.runner.elo = result.new_elo
            result.runner.active = True
            result.save()
            result.runner.save()
        elif result.status == "DSQ":
            result.elo_diff = -round(float(result.runner.elo)*0.010, 2)
            result.new_elo = round(float(result.runner.elo) + float(result.elo_diff), 2)
            result.runner.elo = result.new_elo
            result.runner.active = True
            result.save()
            result.runner.save()
        elif result.place == 0:
            result.new_elo = result.runner.elo
            result.elo_diff = 0
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
    with connection.cursor() as cursor:
        cursor.execute("UPDATE elo_runner SET elo = ROUND(elo * 0.985, 2) WHERE active=0;")


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
            compute_elo_diff(ranking)
    print()

def import_all():
    add_courses_json_to_db()
    Runner.objects.all().update(elo=1600.00, number_of_valid_courses=0)
    elo_for_courses()


if __name__ == "__main__":
    import_all()
