FROM python:3.14-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y cron

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

EXPOSE 8001

RUN mkdir /var/log/gunicorn
RUN mkdir /var/run/gunicorn
RUN mkdir /app/static

CMD ["/bin/bash", "-c", "/app/launch.sh"]
