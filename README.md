# Interfab

## Start using docker

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