# ELOrienteering

This project aims to do a classification based of elo calculations of the helga webres results.

## Features yet to be implemented

- [ ] Compare page, add ids of runner in url to be able to share a completed graph
- [ ] Get a graph with distribution of elo (for runner with more than 3 results and active ?) in about page
- [ ] Cronjob to export and delete pageview data
- [ ] sitemap.xml
- [ ] Translation in french + dutch
- [ ] Adding FFCO CN courses
- [ ] Adding FFCO affiliated

## How to contribute

Python 3.10 minimum (to use the same Django version) ! I use python 3.14. Please do a PR if you want to add something or open an issue if you just have some suggestion.

### Launch the project

Create a `.env` file with the following variables:

```txt
PYTHONUNBUFFERED=1
DJANGO_SECRET_KEY="<generate a random key here>"
```

Create a virtual environment with your ide or python command and install the packages in requirements.txt.

```commandline
# In a linux env
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then create the db in the project:

```commandline
python manage.py migrate
```

## some notes


from dataimport.import_data import *
add_courses_json_to_db()

from dataimport.import_data import *
elo_for_courses()

from dataimport.analysis_temp import *
display_course_elo_change(6157)

Runner.objects.all().update(elo=1600.00, number_of_valid_courses=0)

python manage.py makemigrations elo
python manage.py migrate
