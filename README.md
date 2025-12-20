# ELOrienteering

This project aims to do a classification based of elo calculations of the helga webres results.

## Features yet to be implemented

### Requirements before V1

- [x] paginations to have only 100 runners per page with an arrow to fetch the next/previous. (for load time perf)
- [x] about page to explain the project and reference github and helga.
- [x] simple stat of page load to get an idea of the number of calls to this website.

### Short term

- [x] x axis of graphs should be linear in time and not in number of results.
- [x] exclude by default all runners with less than 3 results (to remove the one time team names).
- [x] Use first 3 courses to have a start-elo.
- [x] handle better the relays (only compare with the same startnumber) for elo calculation.
- [x] display the difference of elo gained over the course.
- [x] search a runner with the search button.
- [ ] Only compute new courses instead of everything from the start.
- [ ] Launch a cronjob with django to load courses and recompute elo everyday at 3AM.
- [x] Using cache at least for index/about page
- [ ] add link to "challenge de régularité national" https://hoekx.be/natcrit/

### Long term

- [ ] Graph with dynamic add/remove of runners to compare evolution.
- [ ] prediction of a course based on helga-start.
- [ ] ranking only of abso/bvos licensed runners. 
- [ ] dashboard for a runner with stats
  - number of results
  - highest elo in last 2 years
  - highest gain in last 2 years
  - Number of NCL in last 2 years
  - increase in last 2 years
  - percentile ?
- [ ] Get a graph with distribution of elo (for runner with more than 3 results) and different percentiles
- [ ] merging D & H of a same circuit to have a better comparaison between women and men elo.

## How to contribute

Python 3.10 minimum (to use the same Django version) ! I use python 3.14. Please do a PR if you want to add something or open an issue if you just have some suggestion.

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


In cronjob doing this:
./manage.py shell < import_data.py ?

https://pypi.org/project/django-crontab/

docker build . -t elorienteering
docker run --rm -p 8008:8008 -it elorienteering
