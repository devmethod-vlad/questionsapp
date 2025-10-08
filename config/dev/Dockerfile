# pull official base image
FROM python:3.10-slim-bullseye
WORKDIR /usr/src/questionsapp/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends \
                       nano \
                       cron \
                       supervisor \
                       wget \
                       alien \
                       libaio1 && \
    wget https://download.oracle.com/otn_software/linux/instantclient/2390000/oracle-instantclient-basic-23.9.0.25.07-1.el8.x86_64.rpm && \
    wget https://download.oracle.com/otn_software/linux/instantclient/2390000/oracle-instantclient-devel-23.9.0.25.07-1.el8.x86_64.rpm && \
    alien -i oracle-instantclient-basic-23.9.0.25.07-1.el8.x86_64.rpm && \
    alien -i oracle-instantclient-devel-23.9.0.25.07-1.el8.x86_64.rpm;

ENV LD_LIBRARY_PATH="/usr/lib/oracle/23/client64/lib:${LD_LIBRARY_PATH}"
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

COPY root /etc/cron.d/
RUN chown root:root /etc/cron.d/root
RUN crontab /etc/cron.d/root

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt