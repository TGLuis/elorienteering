import os
import json
from elo.models import Ranking, Course
from elo.fields import CourseStatus
from dataimport.helga_webres import is_relay

def main():
    rankings = Ranking.objects.filter(distance=0,climb=0)
    courses = {x[0] for x in rankings.values_list("course__source_id")}
    for course in courses:
        rankings_of_course = Ranking.objects.filter(course__source_id=course)
        if all([r.distance == 0 and r.climb == 0 for r in rankings_of_course]):
            try:
                with open(f"dataimport/data/courses/helga/{course}.json") as f:
                    course_json = json.load(f)
                categories = course_json["categories"]
                if all([not is_relay(category) for category in categories.values()]):
                    print(f"{Course.objects.get(source_id=course)} {Course.objects.get(source_id=course).source_id}")
                    c = Course.objects.get(pk=course)
                    c.status = CourseStatus.TODOWNLOAD
                    c.save()
                    os.remove(f"dataimport/data/courses/helga/{course}.json")
            except:
                print(f"Couldn't load course with helga id {course}")
