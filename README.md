# docker homelab manager

[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![CI](https://github.com/mrllama123/docker-homelab-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/mrllama123/docker-homelab-manager/actions/workflows/ci.yml)

A simple web app to manage homelab docker services. I wrote this as portainer, Which i was using for managing my services on my homelab, Didn't have docker volume management i.e backup and restore and all the other docker volume backup and restore tools were too complicated for my needs.

Right now only supports volume backup and restore but I plan to add docker compose support and other features in the future.

## dev setup

### requirements

- [poetry](https://python-poetry.org/docs/#installation)
- [docker](https://docs.docker.com/get-docker/)
- python >=3.11

### setup

setup the project with poetry

```bash
# install dependencies
poetry install
```

create a `.env` file in the root of the project with the following content

```bash
# local directory to store backups
BACKUP_DIR=/path/to/repo/backup
# local directory to store the databases
DB_DIR=/path/to/repo/db
# the sqlalchemy url for the main database file
DATABASE_URL=sqlite:////path/to/repo//db/database.db
# the sqlalchemy url for the apschedule job store
APSCHEDULE_JOBSTORE_URL=sqlite:////path/to/repo/db/schedule.db
```


### running the app locally

(Recommended way) This will start the app in a docker container with hot reloading and run a database migration on startup

```bash
# run the app
poe dev
```

you can also run it locally without docker, Which will run the same commands 
    
```bash
# run the app
poe local-dev
```

> **Note:** If you try to run the app locally with docker then using the same files for the database and backup directories as the container will cause permission issues. You will need to change the permissions of the files to allow the container to access them.

### running tests

```bash
# run tests
poe test
```

### formatting and linting

To run black and isort on codebase:

```bash
# format the code
poe format
```

To run linting:

```bash 
# lint the code
poe lint
```

### database migrations

To make it easy there is some poe tasks to run the migrations:

Run migrationthe

```bash
# run the migrations
poe migrate
```

Create a new migration revision

```bash
# create a new migration revision
poe revision "<revision message here>"
```

Rollback the last migration

```bash
# rollback the last migration
poe downgrade
```

To find out all options for tasks run `poe --help`


### running the app in production

there is a example [docker-compose file](./docker-compose.yml) in the root of the project that you can use to run the app in production

## database structure

See [database.md](./docs/database.md) for a diagram and explanation of the database structure

## License

Copyright © 2023, Bob Bruce

This project is licensed under the [GNU GPL v3+](https://github.com/mrllama123/docker-homelab-manager/blob/main/LICENSE.txt).

In short, this means you can do anything with it (distribute, modify, sell) but if you were to publish your changes, you must make the source code and build instructions readily available.

If you are a company using this project and want an exception, email me at [piesrule123@gmail.com](mailto:piesrule123@gmail.com) and we can discuss.
