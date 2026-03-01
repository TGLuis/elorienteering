import json
import os
import requests
import xmltodict
from elo.models import Runner

ov_url = "https://www.opunch.org/organization/OV/members?key={}"
frso_url = "https://www.opunch.org/organization/FRSO/members?key={}"


def import_fede_members(fede_members, fede_name):
    for competitor in fede_members["CompetitorList"]["Competitor"]:
        name = f"{competitor['Person']['Name']['Given']} {competitor['Person']['Name']['Family']}"
        try:
            runner = Runner.objects.get(fullname=name)
            runner.abso = competitor["Organisation"]["Id"]["@type"] == "ABSO"
            runner.fede = fede_name
            runner.club = competitor["Organisation"]["ShortName"]
            runner.nationality = competitor["Person"]["Nationality"]["@code"]
            runner.sex = competitor["Person"]["@sex"]
            runner.category = competitor["Class"]["Name"]
            runner.save()
        except Runner.DoesNotExist:
            print("Runner does not have any result yet")
        except Exception as e:
            print("Exception in get_runner_from_db")
            print(e)
            print(name)
            exit()


def import_be():
    key = os.environ.get("OPUNCH_KEY")
    # TODO cleanup runners which are not anymore on the list !
    ov_request = requests.get(ov_url.format(key))
    fede_members = xmltodict.parse(ov_request.content)
    with open("dataimport/data/ov.json", "w+") as f:
        json.dump(fede_members, f)
    import_fede_members(fede_members, "OV")
    frso_request = requests.get(frso_url.format(key))
    fede_members = xmltodict.parse(frso_request.content)
    with open("dataimport/data/frso.json", "w+") as f:
        json.dump(fede_members, f)
    import_fede_members(fede_members, "FRSO")


if __name__ == "__main__":
    import_be()
