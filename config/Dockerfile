FROM python:3.11-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.7.22 /uv /uvx /bin/

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
    TZ=Europe/Moscow \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/usr/src/questionsapp/.venv/bin:$PATH"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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
COPY pyproject.toml pyproject.toml
RUN uv sync --no-dev --no-install-project
ENV http_proxy='' https_proxy='' HTTP_PROXY='' HTTPS_PROXY=''

FROM base AS dev

FROM base AS prod
COPY . .

FROM prod AS cron
RUN cp /usr/src/questionsapp/config/root /etc/cron.d/root \
    && chown root:root /etc/cron.d/root \
    && crontab /etc/cron.d/root
CMD ["./entry.sh"]
