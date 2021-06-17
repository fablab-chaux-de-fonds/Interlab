# Interfab

## Start using docker

```shell
$ docker-compose build
```

```shell
$ docker-compose up -d
```

## Use manage.py inside docker instance

```shell
$ docker exec -it interlab_web_1 python manage.py migrate
```

## Import users from fabmanager

Create the temporary database of fabmanager
```shell
$ docker exec -it -u postgres interlab_db_1 psql
postgres=#create database fablab_development;
```

Restore existing database backup 
```shell
zcat fabmanager.psql.gz | docker exec -i -u postgres  interlab_db_1 psql -d fablab_development
```

Execute import script
```shell
docker exec -i interlab_web_1 python manage.py shell < tools/fabmanager-import.py
```

