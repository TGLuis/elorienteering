pip install --no-cache-dir -r /app/requirements.txt
python manage.py collectstatic --noinput
cron
printenv >> /etc/environment
python manage.py crontab add
echo "Starting app"
#python manage.py runserver --insecure 8001
gunicorn -c /app/config/gunicorn/dev.py
