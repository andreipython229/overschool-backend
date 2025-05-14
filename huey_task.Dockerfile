FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y lsb-release wget gnupg build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list; \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -; \
    apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client-15 \
        libpq-dev \
        gcc; \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY huey_configuration .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8002
CMD huey_consumer.py config.main.huey
