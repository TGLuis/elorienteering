import os
import json
import re
import logging

from time import sleep

import requests
import urllib.parse

from datetime import datetime, time


DIR_PATH = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
logger = logging.getLogger(__name__)


def download_courses():
    urls = [
        "https://www.helga-o.com/start-api/ws-complist.php?country=BEL"
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
        logger.info(response)
        # logger.info(response.json())
        logger.info(response.text)



if __name__ == "__main__":
    download_courses()