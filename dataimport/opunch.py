import json
import os
import logging
import requests
import xmltodict
from elo.models import Runner, Affiliation

ov_url = "https://www.opunch.org/organization/OV/members?key={}"
frso_url = "https://www.opunch.org/organization/FRSO/members?key={}"
logger = logging.getLogger(__name__)


def import_fede_members(fede_members, fede_name):
    for competitor in fede_members["CompetitorList"]["Competitor"]:
        name = f"{competitor['Person']['Name']['Given']} {competitor['Person']['Name']['Family']}"
        try:
            runner = Runner.objects.get(fullname=name)
            runner.nationality = competitor["Person"]["Nationality"]["@code"]
            runner.sex = competitor["Person"]["@sex"]
            runner.category = competitor["Class"]["Name"]
            runner.save()
            affiliation = Affiliation.objects.get(country="BEL", runner=runner)
        except Runner.DoesNotExist:
            logger.info("Runner does not have any result yet")
            continue
        except Affiliation.DoesNotExist:
            affiliation = Affiliation()
            affiliation.country = "BEL"
            affiliation.runner = runner
        except Exception as e:
            logger.error("Exception in get_runner_from_db")
            logger.error(e)
            logger.debug(name)
            exit()
        affiliation.fede = fede_name
        affiliation.club = competitor["Organisation"]["ShortName"]
        affiliation.save()


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
