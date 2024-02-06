
FROM python:3.11 as requirements-stage


WORKDIR /tmp


RUN pip install poetry


COPY ./pyproject.toml ./poetry.lock* /tmp/


RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.11


WORKDIR /code


COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

COPY ./src /code/src
COPY ./migrations /code/migrations
COPY ./alembic.ini /code/alembic.ini

LABEL org.opencontainers.image.description = "A simple API to manage docker containers" 
LABEL org.opencontainers.image.source = "https://github.com/mrllama123/docker-homelab-manager"
LABEL org.opencontainers.image.licenses="GPL-3.0" 
