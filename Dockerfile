# syntax=docker/dockerfile:1.7

FROM python:3.11-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.7.22 /uv /uvx /bin/

ARG http_proxy
ARG https_proxy
ARG no_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV http_proxy=${http_proxy} \
    https_proxy=${https_proxy} \
    no_proxy=${no_proxy} \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY}

WORKDIR /usr/src/questionsapp

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venvs/questionsapp \
    PATH="/opt/venvs/questionsapp/bin:$PATH"


RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo "${TZ}" > /etc/timezone

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libaio1 \
        wget \
        alien \
    && wget -q -O /tmp/instantclient-basiclite.rpm \
        https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-basiclite-19.8.0.0.0-1.x86_64.rpm \
    && wget -q -O /tmp/instantclient-devel.rpm \
        https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-devel-19.8.0.0.0-1.x86_64.rpm \
    && alien -i /tmp/instantclient-basiclite.rpm \
    && alien -i /tmp/instantclient-devel.rpm \
    && rm -f /tmp/instantclient-*.rpm \
    && apt-get purge -y --auto-remove wget alien \
    && rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH="/usr/lib/oracle/19.8/client64/lib:${LD_LIBRARY_PATH}"

FROM base AS deps-dev
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

FROM base AS deps-prod
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM deps-dev AS dev
ENV http_proxy='' \
    https_proxy='' \
    no_proxy='' \
    HTTP_PROXY='' \
    HTTPS_PROXY='' \
    NO_PROXY=''

FROM deps-prod AS prod
ENV http_proxy='' \
    https_proxy='' \
    no_proxy='' \
    HTTP_PROXY='' \
    HTTPS_PROXY='' \
    NO_PROXY=''

RUN chmod +x ./entry.sh

FROM prod AS cron
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/* \
    && cp /usr/src/questionsapp/config/root /etc/cron.d/root \
    && chown root:root /etc/cron.d/root \
    && chmod 0644 /etc/cron.d/root \
    && crontab /etc/cron.d/root

CMD ["./entry.sh"]