import re
import os
import math
import requests
import chardet

import pandas as pd

from datetime import datetime, time, timedelta
import pytz

from elo.models import Course, Runner, Ranking, Result
from elo.fields import *

DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
separator = "-=-"

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "fr-BE,fr;q=0.9,en-BE;q=0.8,en;q=0.7,nl-BE;q=0.6,nl;q=0.5,es-ES;q=0.4,es;q=0.3,sl-SI;q=0.2,sl;q=0.1,fr-FR;q=0.1,en-US;q=0.1",
    "dnt": "1",
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
cookies = {
    # "csrftoken": "",
    # "sessionid": ""
}

row_pattern = re.compile('<tr class="row[12]">((?:.|\n)*?)</tr>')
course_pattern = re.compile('<td>(.*?)</td>(?:.|\n)*?href="/course/(\\d+)/">(.*?)</a>(?:.|\n)*?<td>(?:.|\n)*?</td>(?:.|\n)*?<td>(.*?)</td>(?:.|\n)*?<td>(.*?)</td>(?:.|\n)*?<td>(.*?)</td>(?:.|\n)*?<td>(.*?)</td>')

def download_courses():
    url_course = "https://cn.ffcorientation.fr/resultats_csv/{}/"
    courses_to_download = Course.objects.filter(source=Source.FFCO_CN, status=CourseStatus.TODOWNLOAD)
    courses_to_download_ids = [str(c.source_id) for c in courses_to_download]
    print(f"{courses_to_download_ids=}")
    for year in range(2011, datetime.now().year+1):
        print(f"{year=}")
        session = requests.Session()
        response = session.get(f"https://cn.ffcorientation.fr/course/?season={year}", headers=headers, cookies=cookies)
        rows = row_pattern.findall(response.text)
        for row in rows:
            info = course_pattern.findall(row)
            if not info:
                continue # maybe investigate if necessary to recover from here
            info = info[0]
            course_id = info[1]
            filename = f"{DIR_PATH}/data/courses/ffco_cn/{course_id}.csv"
            if os.path.exists(filename) and course_id not in courses_to_download_ids:
                continue
            if course_id in courses_to_download_ids:
                courses_to_download.filter(source_id=course_id).update(status=CourseStatus.TOIMPORT)
            response = requests.get(url_course.format(course_id), headers=headers, cookies=cookies)
            if response.ok:
                date, name, location, type, subtype = info[0], info[2], info[3], info[5],info[6]
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"{date}{separator}{name}{separator}{location}{separator}{type}{separator}{subtype}\n")
                    f.write(preprocess(response.content, response.text))

def get_unencoded(content):
    detections = chardet.detect_all(content.replace(b";", b" ")[:150], no_match_encoding="utf-8")
    for detection in detections:
        try:
            return content.decode(encoding=detection["encoding"])
        except:
            pass
    return None

def preprocess(csv_content, csv_text_original):
    csv_text = get_unencoded(csv_content)
    if csv_text is None:
        csv_text = csv_text_original
    lines = csv_text.split("\n")
    header_length = len(lines[0].split(";"))
    return "\n".join([
        ";".join(line.split(";")[:header_length])
        for line in lines
    ])

def get_courses_ids():
    all_filenames = []
    for (dirpath, dirnames, filenames) in os.walk(f"{DIR_PATH}/data/courses/ffco_cn"):
        all_filenames = filenames
    all_courses = []
    for filename in all_filenames:
        try:
            with open(f"{DIR_PATH}/data/courses/ffco_cn/{filename}", encoding="utf-8") as f:
                date = datetime.strptime(f.readline().split(separator)[0], "%d/%m/%Y")
                all_courses.append({"id": filename.split(".")[0], "date": date})
        except Exception as e:
            print(e)
            print(filename)
            exit()
    all_courses.sort(key=lambda x: x["date"])
    return [course["id"] for course in all_courses]

def get_type(text):
    if text == "Pédestre":
        return CourseType.FOOTO
    if text == "VTT":
        return CourseType.MTBO
    if text == "Ski":
        return CourseType.SKIO
    return CourseType.UNKNOWN

def get_subtype(text):
    if text == "LD":
        return CourseSubType.LONG
    if text == "MD":
        return CourseSubType.MIDDLE
    if text == "Sprint":
        return CourseSubType.SPRINT
    if text == "Nuit":
        return CourseSubType.NIGHT
    return CourseSubType.UNKNOWN

def get_runner_from_db(fullname, ident_db):
    if ident_db is not None and ident_db == 0:
        ident_db = None
    if ident_db is not None:
        runners = Runner.objects.filter(fullname=fullname, ffco_id=ident_db)
        if len(runners)==1:
            return runners[0]
        elif len(runners) > 1:
            print("Too much match for the runner !")
            return None
    runners = Runner.objects.filter(fullname=fullname)
    if len(runners) == 1:
        if ident_db is not None and runners[0].ffco_id is not None and runners[0].ffco_id != ident_db:
            print(f"!! Two ffco_id for runner {runners[0].fullname} {ident_db=} and {runners[0].ffco_id} !!")
            runner = Runner(fullname=fullname, ffco_id=ident_db)
            runner.save()
            return runner
        runners[0].ffco_id = ident_db
        runners[0].save()
        return runners[0]
    elif ident_db is not None and len(runners) > 1:
        for runner in runners:
            if runner.ffco_id == ident_db:
                return runner
    # default create new runner
    runner = Runner(fullname=fullname, ffco_id=ident_db)
    runner.save()
    return runner

def set_result_time(result, row):
    if type(row["Temps"]) != str:
        return None
    t = row["Temps"].strip()
    if len(t) == 7:
        t = "0"+t
    elif len(t) == 5:
        t = "00:"+t
    elif len(t) == 4:
        t = "00:0"+t
    try:
        result.time = time.fromisoformat(t)
    except:
        result.time = None

def set_result_status(result, row):
    status = None
    if "Evaluation" in row:
        status = row["Evaluation"]
    elif "Classer" in row:
        status = row["Classer"]
    if math.isnan(status):
        status = 3
    if status == 0:
        result.status = "OK"
    elif status == 1:
        result.status = "DNS"
    elif status == 2:
        # abandon
        result.status = "NCL"
    elif status == 3:
        # pm
        result.status = "NCL"
    elif status == 4:
        # ??
        result.status = "NCL"
    elif status == 5:
        # hors delais
        result.status = "NCL"
    elif status > 10:
        # ??? wtf
        result.status = "UNKNOWN"
    else:
        raise Exception(f"{row=}\n{status=}")

def bad_lines(bad_line: list[str]) -> list[str] | None:
    return bad_line

def get_fullname(row):
    if "Prénom" in row:
        prenom = row["Prénom"]
    else:
        print(row)
        raise Exception("No Prénom in row")
    if "NOM" in row:
        if type(row["NOM"]) == float:
            return "Vacant"
        return f'{prenom} {row["NOM"].upper()}'
    if "Nom" in row:
        if type(row["Nom"]) == float:
            return "Vacant"
        return f'{prenom} {row["Nom"].upper()}'
    raise Exception("noname")

def get_ffco_id(row):
    if "Ident. base de données" in row:
        ident = row["Ident. base de données"]
    else:
        raise Exception("No ident base de donnees")
    if ident is None:
        return None
    if type(ident) == int:
        return ident
    if type(ident) == float:
        if math.isnan(ident):
            return None
        return int(ident)
    if type(ident) == str:
        try:
            return int(ident)
        except ValueError:
            return None
    return None

def attribute_positions(results):
    non_zero = [result for result in results if result.time is not None and result.status == "OK"]
    non_zero.sort(key=lambda x: x.time)
    position, egalite = 0, 1
    old_time = time.fromisoformat("00:00:00.000")
    for res in non_zero:
        if res.time > old_time:
            position += egalite
            egalite = 1
        elif res.time == old_time:
            egalite += 1
        res.place = position
        old_time = res.time
    results = non_zero + sorted([result for result in results if result.place == 0], key=lambda x: x.status, reverse=True)
    return results

def is_duplicate(course_date, course_id, df):
    date_before = course_date.isoformat(sep=" ", timespec="seconds")
    date_after = (course_date + timedelta(days=1)).isoformat(sep=" ", timespec="seconds")
    courses_same_date = Course.objects.exclude(source=Source.FFCO_CN).filter(date__gte=date_before,date__lte=date_after)
    if len(courses_same_date) < 1:
        return False
    circuit_names = list(df["Circuit"].unique())
    for course in courses_same_date:
        rankings = Ranking.objects.filter(course=course)
        rankings_name = [r.name for r in rankings]
        for name in circuit_names:
            if name not in rankings_name:
                break
        else:
            runner_verified, nrows = 0, 0
            for _, row in df.iterrows():
                circuit_name = row["Circuit"]
                ranking = rankings.filter(name=circuit_name)[0]
                runners = Runner.objects.filter(fullname=get_fullname(row))
                if len(runners) == 0:
                    continue  # This is not a duplicate
                if len(runners) > 1:
                    continue  # pass this runner name
                runner = runners[0]
                if len(Result.objects.filter(ranking=ranking,runner=runner)) == 1:
                    runner_verified += 1
                nrows += 1
                if runner_verified > 5:
                    break
                if nrows > 10:
                    break
            if runner_verified > 5:
                print(f"FFCO_CN {course_id=} is duplicate of {course}")
                return True
    return False


def import_courses_in_db():
    all_ids = get_courses_ids()
    for course_id in all_ids:
        filename = f"{DIR_PATH}/data/courses/ffco_cn/{course_id}.csv"
        with open(filename, encoding="utf-8") as f:
            info = f.readline().split(separator)
            first_line = f.readline()
        filesep = ";" if first_line.count(";") > first_line.count(",") else ","
        course_date, course_name, course_location = datetime.strptime(info[0], "%d/%m/%Y"), info[1], info[2]
        course_date = course_date.astimezone(pytz.timezone("Europe/Brussels"))
        df = pd.read_csv(filename, skiprows=1, sep=filesep, engine='python', on_bad_lines=bad_lines)
        if is_duplicate(course_date, course_id, df):
            continue
        Course.objects.filter(date__gte=course_date.isoformat(sep=" ", timespec="seconds"))
        db_course = Course.objects.filter(source=Source.FFCO_CN,source_id=course_id).first()
        if db_course is not None:
            if db_course.status != CourseStatus.TOIMPORT:
                continue
            else:
                db_course.delete()
        print(course_id, end=", ", flush=True)
        course_type, course_subtype = get_type(info[3].strip()), get_subtype(info[4].strip())
        # print(f'{course_name=}\t{course_date=}\t{course_location=}\t{course_type=}\t{course_subtype=}')
        course = Course()
        course.source_id = course_id
        course.name = course_name
        course.date = course_date
        course.location = course_location
        course.status = CourseStatus.TOPROCESS
        course.type = course_type
        course.subtype = course_subtype
        course.source = Source.FFCO_CN
        course.save()
        results = []
        if "m" in df and "km" in df:
            df_by_circuit = df.groupby(["Circuit", "km", "m"])
        else:
            df_by_circuit = df.groupby(["Circuit"])
            df_by_circuit = [((a, 0, 0), c) for (a,), c in df_by_circuit]
        for (circuit_name, distance, climb), df_circuit in df_by_circuit:
            # print(f"{circuit_name=}\t{distance=}\t{climb=}m")
            try:
                if type(distance) not in [float, int]:
                    distance = float(distance.replace(",", ".").replace(";", "."))
                if distance > 1000:
                    distance = float(distance) / 1000
            except ValueError:
                try:
                    # migth be just one column off
                    circuit_name, distance, climb = distance, float(climb.replace(",", ".").replace(";", ".")), 0
                except:
                    continue
            ranking = Ranking()
            ranking.course = course
            ranking.name = circuit_name
            ranking.distance = int(distance * 1000)
            ranking.climb = climb
            ranking_results = []
            for _, row in df_circuit.iterrows():
                fullname = get_fullname(row)
                if "Vacant" in fullname:
                    continue
                ffco_id = get_ffco_id(row)
                runner = get_runner_from_db(fullname, ffco_id)
                # print(f'{ runner=}\t{row["Temps"]}')
                result = Result()
                result.ranking = ranking
                result.runner = runner
                result.place = 0
                set_result_time(result, row)
                set_result_status(result, row)
                result.date = course.date
                ranking_results.append(result)
            if ranking_results:
                attribute_positions(ranking_results)
                ranking.save()
                results.extend(ranking_results)
        if results:
            Result.objects.bulk_create(results)
        else:
            course.delete()

if __name__ == "__main__":
    download_courses()