# ELOrienteering

This project aims to do a classification based of elo calculations of the helga webres results.

## Features yet to be implemented

### Short term

- paginations to have only 100 runners per page with an arrow to fetch the next/previous. (for load time perf)
- exclude by default all runners with less than 3 results (to remove the one time team names).
- handle better the relays (only compare with the same startnumber) for elo calculation.
- display the difference of elo gained over the course.
- search a runner with the search button.
- about page to explain the project and reference github and helga.
- x axis of graphs should be linear in time and not in number of results.
- Only compute new courses instead of everything from the start.
- Launch a cronjob with django to load courses and recompute elo everyday at 3AM.

### Long term

- Graph with dynamic add/remove of runners to compare evolution.
- prediction of a course based on elo.
- merging D & H of a same circuit to have a better comparaison between women and men elo.

## How to contribute

Python 3.10 minimum ! I use python 3.14. Please do a PR if you want to add someting or open an issue if you just have some suggestion.

## some notes


from dataimport.import_data import *
add_courses_json_to_db()

from dataimport.import_data import *
elo_for_courses()


Runner.objects.all().update(elo=1500.00)

python manage.py makemigrations elo
python manage.py migrate


In cronjob doing this:
./manage.py shell < import_data.py ?

https://pypi.org/project/django-crontab/
