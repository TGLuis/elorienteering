Python 3.10 minimum !


from dataimport.import_data import *
add_courses_json_to_db()



from dataimport.import_data import *
elo_for_courses()


from dataimport.import_data import *
update_runners_inactives(2022)


Runner.objects.all().update(elo=1500.00)

python manage.py makemigrations elo
python manage.py migrate


In cronjob doing this:
./manage.py shell < import_data.py ?

https://pypi.org/project/django-crontab/

SELECT elo_runner.id FROM elo_runner JOIN elo_result ON elo_runner.id=elo_result.runner_id WHERE elo_result.date >= '{beginning_of_last_year.strftime("%Y-%m-%d")}' AND elo_result.date < '{beginning_of_this_year}')