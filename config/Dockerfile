FROM python:3.10-slim-bookworm AS base

ARG http_proxy
ARG https_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV http_proxy=${http_proxy} \
    https_proxy=${https_proxy} \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY}

WORKDIR /usr/src/questionsapp/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN python -m pip install --upgrade pip

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates nano cron supervisor wget alien libaio1 \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O /tmp/instantclient-basiclite.rpm \
        https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-basiclite-19.8.0.0.0-1.x86_64.rpm \
    && wget -q -O /tmp/instantclient-devel.rpm \
        https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-devel-19.8.0.0.0-1.x86_64.rpm \
    && alien -i /tmp/instantclient-basiclite.rpm \
    && alien -i /tmp/instantclient-devel.rpm \
    && rm -f /tmp/instantclient-*.rpm

ENV LD_LIBRARY_PATH="/usr/lib/oracle/19.8/client64/lib:${LD_LIBRARY_PATH}"

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
ENV http_proxy='' https_proxy='' HTTP_PROXY='' HTTPS_PROXY=''

FROM base AS cron
COPY root /etc/cron.d/
RUN chown root:root /etc/cron.d/root
RUN crontab /etc/cron.d/root
CMD ["./entry.sh"]