FROM python:3.14-slim

RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY manage.py .
COPY elorienteering ./elorienteering
COPY elo ./elo
COPY db.sqlite3 .
COPY config ./config


EXPOSE 8008

RUN python manage.py createsuperuser \
    && mkdir /var/log/gunicorn \
    && mkdir /var/run/gunicorn \
    && mkdir /app/static \
    && python manage.py collectstatic --noinput

CMD ["gunicorn", "-c", "/app/config/gunicorn/dev.py"]
