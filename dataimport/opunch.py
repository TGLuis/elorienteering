import json
import os
import logging
import requests
import xmltodict
from elo.models import Runner, Affiliation

ov_url = "https://www.opunch.org/organization/OV/members?key={}"
frso_url = "https://www.opunch.org/organization/FRSO/members?key={}"
luxo_url = "https://www.opunch.org/organization/LUXO/members?key={}"
logger = logging.getLogger(__name__)

import country_converter as coco
cc = coco.CountryConverter()
ioc_iso3 = cc.get_correspondence_dict('IOC', 'ISO3')

os.environ["OPUNCH_KEY"] = "1f4eb968-755a-47ae-9a22-8c71c69008a1"

def import_fede_members(country, fede_members, fede_name):
    for competitor in fede_members["CompetitorList"]["Competitor"]:
        name = f"{competitor['Person']['Name']['Given']} {competitor['Person']['Name']['Family'].upper()}"
        try:
            runner = Runner.objects.get(fullname=name)
            runner.nationality = ioc_iso3[competitor["Person"]["Nationality"]["@code"]][0]
            runner.sex = competitor["Person"]["@sex"]
            runner.category = competitor["Class"]["Name"]
            runner.save()
            affiliation = Affiliation.objects.get(country=country, runner=runner)
        except Runner.DoesNotExist:
            logger.info("Runner does not have any result yet")
            continue
        except Affiliation.DoesNotExist:
            affiliation = Affiliation()
            affiliation.country = country
            affiliation.runner = runner
        except Exception as e:
            logger.error("Exception in get_runner_from_db")
            logger.error(e)
            logger.debug(name)
            exit()
        affiliation.fede = fede_name
        affiliation.club = competitor["Organisation"]["ShortName"]
        affiliation.save()


def import_opunch():
    key = os.environ.get("OPUNCH_KEY")
    # TODO cleanup runners which are not anymore on the list !
    ov_request = requests.get(ov_url.format(key))
    fede_members = xmltodict.parse(ov_request.content)
    with open("dataimport/data/ov.json", "w+") as f:
        json.dump(fede_members, f)
    import_fede_members("BEL", fede_members, "OV")

    frso_request = requests.get(frso_url.format(key))
    fede_members = xmltodict.parse(frso_request.content)
    with open("dataimport/data/frso.json", "w+") as f:
        json.dump(fede_members, f)
    import_fede_members("BEL", fede_members, "FRSO")

    luxo_request = requests.get(luxo_url.format(key))
    fede_members = xmltodict.parse(luxo_request.content)
    with open("dataimport/data/luxo.json", "w+") as f:
        json.dump(fede_members, f)
    import_fede_members("LUX", fede_members, "LUXO")


if __name__ == "__main__":
    import_opunch()
