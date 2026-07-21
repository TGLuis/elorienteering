import os
import json
import re
import logging
from collections import defaultdict

from time import sleep

import requests
import urllib.parse

from datetime import datetime, time

from dataimport.calculate import DIR_PATH
from elo.models import Course, Runner, Ranking, Result
from elo.fields import *

logger = logging.getLogger(__name__)
DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
countries = ["BEL", "NED", "FRA", "LUX", "GER", "SWE"]

def download_courses():
    url = "https://helga-o.com/webres-api/ws-complist.php?top=100"
    courses_to_download = Course.objects.filter(source=SourceType.HELGA_WEBRES, status=CourseStatus.TODOWNLOAD)
    courses_to_download_ids = [str(c.source_id) for c in courses_to_download]
    logger.debug(f"{courses_to_download_ids=}")
    response = requests.get(url)
    course_ids = [key for key, value in response.json()["Events"].items() if value["isLive"]==0 and value["CountryCode"] in countries]
    for course_id in course_ids:
        filename = f"{DIR_PATH}/data/courses/helga/{course_id}.json"
        if (not os.path.exists(filename)) or (course_id in courses_to_download_ids):
            if course_id in courses_to_download_ids:
                courses_to_download.filter(source_id=course_id).update(status=CourseStatus.TOIMPORT)
            with open(filename, "w") as f:
                response = requests.get(f"https://helga-o.com/webres-api/ws.php?lauf={course_id}")
                f.write(response.text)
            pre_process(course_id, filename)
            sleep(2)


def get_courses_ids():
    all_filenames = []
    for (dirpath, dirnames, filenames) in os.walk(f"{DIR_PATH}/data/courses/helga"):
        all_filenames = filenames
    all_courses = []
    for filename in all_filenames:
        try:
            with open(f"{DIR_PATH}/data/courses/helga/{filename}") as f:
                f.readline()
                date = datetime.fromisoformat(f.readline().split('"')[3])
                all_courses.append({"id": filename.split(".")[0], "date": date})
        except Exception as e:
            logger.error(e)
            logger.debug(filename)
            exit()
    all_courses.sort(key=lambda x: x["date"])
    return [course["id"] for course in all_courses]


def get_helga_id(runner_name):
    response = requests.get(f"https://helga-o.live/searchrunner.php?q={urllib.parse.quote(runner_name, safe='')}")
    logger.info(f"Requesting helga_id for runner: {runner_name}")
    if response.text == "" and "'" in runner_name:
        user_name_request = runner_name.replace("'", "&#39;")
        response = requests.get(f"https://helga-o.live/searchrunner.php?q={urllib.parse.quote(user_name_request, safe='')}")
        return int(re.findall(r"runner=(\d+)[^<]*?>" + re.escape(user_name_request), response.text)[0])
    else:
        return int(re.findall(r"runner=(\d+)[^<]*?>" + re.escape(runner_name), response.text)[0])


def is_vacant_result(result_json):
    return "VACANT" in result_json["name"] and (result_json["ageclass"] in [None, "-", ""] or (
                result_json["status"] != "OK" and result_json["time"] is None))


def merge_DH(categories):
    category_names = { re.findall(r"[HD]:(.*)", x)[0] for x in categories.keys() }
    new_categories = {}
    for category_name in category_names:
        new_categories[category_name] = merge_categories(category_name, categories.get("D:"+category_name), categories.get("H:"+category_name))
    return new_categories


def merge_categories(name, category1, category2):
    if category1 is None:
        category2["name"] = name
        return category2
    if category2 is None:
        category1["name"] = name
        return category1
    results = reattribute_positions(category1.get("results", []) + category2.get("results", []))
    return {
        "name": name,
        "distance": category1["distance"],
        "climb": category1["climb"],
        "results" : results
    }


def reattribute_positions(results):
    non_zero = [result for result in results if result["position"] != 0 and result["status"] == "OK"]
    non_zero.sort(key=lambda x: (time.fromisoformat(x["time"])))
    position, egalite = 0, 1
    old_time = time.fromisoformat("00:00:00.000")
    for res in non_zero:
        if time.fromisoformat(res["time"]) > old_time:
            position += egalite
            egalite = 1
        elif time.fromisoformat(res["time"]) == old_time:
            egalite += 1
        res["position"] = position
        old_time = time.fromisoformat(res["time"])
    results = non_zero + sorted([result for result in results if result["position"] == 0], key=lambda x: x["status"],
                                reverse=True)
    return results


def is_relay(category):
    startnumbers = defaultdict(lambda: 0)
    for result in category['results']:
        if result.get('startnumber') is None:
            return False
        startnumbers[result.get('startnumber')] += 1
    return all([ val > 1 for val in startnumbers.values()])


def split_relay(categories):
    new_categories = defaultdict(dict)
    for category_name, category in categories.items():
        for res in category["results"]:
            if is_vacant_result(res):
                continue
            startnumber = res["startnumber"]
            if new_categories.get(f"{category_name}.{startnumber}") is None:
                new_categories[f"{category_name}.{startnumber}"] = {
                    "name": f"{category['name']}.{startnumber}",
                    "distance": category["distance"],
                    "climb": category["climb"],
                    "results": []
                }
            new_categories[f"{category_name}.{startnumber}"]["results"].append(res)
    for name, category in new_categories.items():
        new_categories[name]["results"] = reattribute_positions(category["results"])
    return new_categories


def pre_process(helga_id, course_file):
    with open(course_file) as f:
        course_json = json.load(f)
    categories = course_json["categories"]
    if all([re.findall(r"[HD]:.*", category_name) for category_name in categories.keys()]):
        logger.info(f"Merging HD for course: {helga_id} - {course_json['name']}")
        course_json["categories"] = merge_DH(categories)
        with open(course_file, "w+") as f:
            json.dump(course_json, f, indent=4)
    elif all([is_relay(category) for category in categories.values()]):
        logger.info(f"Splitting relay for course: {helga_id} - {course_json['name']}")
        course_json["categories"] = split_relay(categories)
        with open(course_file, "w+") as f:
            json.dump(course_json, f, indent=4)

def iterate_over_all_course_files():
    all_filenames = []
    for (dirpath, dirnames, filenames) in os.walk(f"{DIR_PATH}/data/courses/helga"):
        all_filenames = filenames
    for filename in all_filenames:
        pre_process(filename.split(".")[0], f"{DIR_PATH}/data/courses/helga/{filename}")


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
        logger.error("Exception in get_runner_from_db")
        logger.error(e)
        logger.debug(runner_name)
        exit()


def import_courses_in_db():
    all_ids = get_courses_ids()
    for course_id in all_ids:
        with open(f"{DIR_PATH}/data/courses/helga/{course_id}.json") as f:
            db_course = Course.objects.filter(source_id=course_id).first()
            if db_course is not None:
                if db_course.status != CourseStatus.TOIMPORT:
                    continue
                else:
                    db_course.delete()
            logger.info(course_id, end=", ", flush=True)
            course_json = json.load(f)
            course = Course()
            course.source_id = course_id
            course.name = course_json["name"]
            course.date = datetime.strptime(course_json["date"], "%Y-%m-%dT%H:%M:%S%z")
            course.location = course_json["location"]
            course.status = CourseStatus.TOPROCESS
            course.type = CourseType.UNKNOWN # TODO add some logic here ?
            course.subtype = CourseSubType.UNKNOWN # TODO add some logic here ?
            course.source = SourceType.HELGA_WEBRES
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
    logger.info("finished")
