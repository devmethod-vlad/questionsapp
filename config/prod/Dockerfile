# pull official base image
FROM python:3.10-slim-buster
WORKDIR /usr/src/questionsapp/
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV http_proxy http://10.0.20.6:80
ENV https_proxy http://10.0.20.6:80
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV NO_PROXY="moodle.emias.ru, 10.1.55.115, 10.2.19.8, 10.2.172.28"
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends nano\
                       cron\
                       supervisor\
                       wget\
                       alien\
                       libaio1 && \
                       wget https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-basiclite-19.8.0.0.0-1.x86_64.rpm && \
    wget https://download.oracle.com/otn_software/linux/instantclient/19800/oracle-instantclient19.8-devel-19.8.0.0.0-1.x86_64.rpm && \
    alien -i oracle-instantclient19.8-basiclite-19.8.0.0.0-1.x86_64.rpm && \
    alien -i oracle-instantclient19.8-devel-19.8.0.0.0-1.x86_64.rpm;
ENV LD_LIBRARY_PATH="/usr/lib/oracle/19.8/client64/lib:${LD_LIBRARY_PATH}"   
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
COPY root /etc/cron.d/
RUN chown root:root /etc/cron.d/root
RUN crontab /etc/cron.d/root
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt