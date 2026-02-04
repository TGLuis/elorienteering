import os
import json
import re
from collections import defaultdict

from time import sleep

import requests
import urllib.parse

from datetime import datetime, time

from elo.models import Course

DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))


def get_new_courses():
    urls = [
        "https://helga-o.com/webres/index.php?year=3&country=BEL&lang=&setfilter=1&orga=0",
        "https://helga-o.com/webres/index.php?year=3&country=FRA&lang=&setfilter=1&orga=0",
        "https://helga-o.com/webres/index.php?year=3&country=GER&lang=&setfilter=1&orga=0",
        "https://helga-o.com/webres/index.php?year=3&country=LUX&lang=&setfilter=1&orga=0",
        "https://helga-o.com/webres/index.php?year=3&country=NED&lang=&setfilter=1&orga=0",
    ]
    for url in urls:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "fr-BE,fr;q=0.9,en-BE;q=0.8,en;q=0.7,nl-BE;q=0.6,nl;q=0.5,es-ES;q=0.4,es;q=0.3,sl-SI;q=0.2,sl;q=0.1,fr-FR;q=0.1,en-US;q=0.1",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
          }
        response = requests.get(url, headers=headers)
        course_ids = sorted(re.findall(r"lauf=(\d+)", response.text))
        for course_id in course_ids:
            filename = f"{DIR_PATH}/data/courses/{course_id}.json"
            if not os.path.exists(filename):
                with open(filename, "w") as f:
                    response = requests.get(f"https://helga-o.com/webres/ws.php?lauf={course_id}")
                    f.write(response.text)
                pre_process(course_id, filename)
                sleep(2)


def get_courses_ids():
    for (dirpath, dirnames, filenames) in os.walk(f"{DIR_PATH}/data/courses"):
        all_filenames = filenames
    all_courses = []
    for filename in all_filenames:
        try:
            with open(f"{DIR_PATH}/data/courses/{filename}") as f:
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
        print(f"Merging HD for course: {helga_id} - {course_json['name']}")
        course_json["categories"] = merge_DH(categories)
        if course_db := Course.objects.filter(helga_id=helga_id):
            course_db.delete()
        with open(course_file, "w+") as f:
            json.dump(course_json, f, indent=4)
    elif all([is_relay(category) for category in categories.values()]):
        print(f"Splitting relay for course: {helga_id} - {course_json['name']}")
        course_json["categories"] = split_relay(categories)
        if course_db := Course.objects.filter(helga_id=helga_id):
            course_db.delete()
        with open(course_file, "w+") as f:
            json.dump(course_json, f, indent=4)

def iterate_over_all_course_files():
    for (dirpath, dirnames, filenames) in os.walk(f"{DIR_PATH}/data/courses"):
        all_filenames = filenames
    for filename in all_filenames:
        pre_process(filename.split(".")[0], f"{DIR_PATH}/data/courses/{filename}")
