import urllib.parse
from datetime import datetime

import requests
import os
from time import sleep
import re
from enum import Enum

class OV(Enum):
    AntwerpOrienteers = "Antwerp Orienteers"
    Borasca = "Borasca"
    Hamok = "hamok"
    KOL = "K.O.L."
    Omega = "Omega"
    Trol = "TROL"
class FRSO(Enum):
    Altair = "Altaïr Orientation"
    Ardoc = "O.L.G. St. Vith ARDOC"
    ASUB = "ASUB"
    Balise10 = "Balise 10"
    CoLiege = "CO Liège"
    COMB = "C.O. Militaire Belge"
    Hermatenae = "Hermathenae"
    HOC = "Hainaut O.C."
    LOST = "LOST"
    OLV = "OLV Eifel"
    Pegase = "Pégase CO"
    SudOLux = "SUD O LUX"
    Thor = "ThOR"


def from_db_to_json_id():
    return # Should not be used anymore only for first import
    with sqlite3.connect("dataimport/data/helga.sqlite3") as conn:
        cur = conn.cursor()
        res = cur.execute("SELECT id, name, elo FROM Runner").fetchall()
        for row in res:
            runner = Runner()
            runner.helga_id = row[0]
            runner.fullname = row[1]
            runner.elo = 1500.00
            runner.save()

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
            if not os.path.exists(f"dataimport/data/courses/{course_id}.json"):
                with open(f"dataimport/data/courses/{course_id}.json", "w") as f:
                    response = requests.get(f"https://helga-o.com/webres/ws.php?lauf={course_id}")
                    f.write(response.text)
                sleep(2)


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
