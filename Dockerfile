FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY nginx.conf /app
COPY ./app /app
COPY ./app/nucapt/static /app/static

ENV APP_CONFIG_FILE /conf/app.conf
