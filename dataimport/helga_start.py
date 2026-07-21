import os
import logging

from datetime import datetime

import requests

from elo.fields import SourceType, CourseStatus, CourseType, CourseSubType
from elo.models import Course, Ranking, Runner, Entry


DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
logger = logging.getLogger(__name__)
countries = ["BEL", "NED", "FRA", "LUX", "GER", "SWE"]


def get_courses_id():
    url = "https://www.helga-o.com/start-api/ws-complist.php"
    response = requests.get(url)
    if not response.ok:
        print(f"Cannot download list of helga-start ! {response.ok=} {response.text}")
        return
    course_ids = []
    print(response)
    print(response.text)
    for id, event_info in response.json()["Events"].items():
        if event_info["CountryCode"] in countries:
            print(f"{id=}\t{event_info['EventDescription']}")
            course_ids.append(id)
    return course_ids


def remove_courses():
    db_courses = Course.objects.filter(source=SourceType.HELGA_START)
    if db_courses is not None:
        db_courses.delete()


def get_runner_from_db(runner_name):
    try:
        return Runner.objects.get(fullname = runner_name)
    except Runner.DoesNotExist:
        runner = Runner(fullname=runner_name)
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


def import_course_in_db(course_id):
    logger.info(course_id)
    response = requests.get(f"https://www.helga-o.com/start-api/ws.php?lauf={course_id}")
    if not response.ok:
        print(f"Can't fetch helga start course {course_id}: {response.text}")
    course_json = response.json()
    course = Course()
    course.source_id = course_id
    course.name = course_json["name"]
    course.date = datetime.strptime(course_json["date"], "%Y-%m-%dT%H:%M:%S%z")
    course.location = course_json["location"]
    course.status = CourseStatus.FUTURE
    course.type = CourseType.UNKNOWN # TODO add some logic here ?
    course.subtype = CourseSubType.UNKNOWN # TODO add some logic here ?
    course.source = SourceType.HELGA_START
    course.save()

    entries = []
    for ranking_json in course_json["categories"].values():
        ranking = Ranking()
        ranking.course = course
        ranking.name = ranking_json["name"]
        ranking.distance = 0
        ranking.climb = 0
        ranking.save()

        for entry_json in ranking_json["starts"]:
            entry = Entry()
            entry.ranking = ranking
            entry.runner = get_runner_from_db(entry_json["name"])
            entry.starttime = entry_json.get("time")
            entry.startnumber = entry_json.get("startnumber")
            entries.append(entry)

    Entry.objects.bulk_create(entries)

def main():
    remove_courses()
    course_ids = get_courses_id()
    for course_id in course_ids:
        import_course_in_db(course_id)

if __name__ == "__main__":
    main()