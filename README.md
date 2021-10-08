# Interfab

## Start using docker

Docker image is using environment variables, copy env.example to .env with your environment values
```shell
$ cp env.example .env
```

```shell
$ docker-compose build
```

```shell
$ docker compose up -d
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
## Generate translation file

### Update PO file with new keys
```shell
docker exec -it interlab_web_1 django-admin makemessages -l fr -e html,txt
```

### Regenerate translation compiled messages
```shell
docker exec -it interlab_web_1 django-admin compilemessages
```

## Frontend 
Documentation: https://www.accordbox.com/blog/definitive-guide-django-and-webpack/

### Development
Install dependencies and run development server

```shell
$ cd frontend
$ npm install
$ npm run start
```

### production

Install dependencies and build
```shell
$ cd frontend
$ npm install
$ npm run build
$ docker exec -it interlab_web_1 python manage.py collectstatic --noinput --clear
```