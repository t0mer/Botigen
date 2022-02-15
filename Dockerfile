FROM techblog/selenium:latest

LABEL maintainer="tomer.klein@gmail.com"

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV EDU_SITE_USER = ""
ENV EDU_SITE_PASSWORD = ""
ENV BOT_TOKEN = ""
ENV ALLOWED_IDS = ""

RUN  pip3 install --upgrade pip --no-cache-dir && \
     pip3 install --upgrade setuptools --no-cache-dir

COPY requirements.txt /tmp

RUN pip3 install -r /tmp/requirements.txt

COPY app /opt/app

WORKDIR /opt/app/

ENTRYPOINT python app.py


