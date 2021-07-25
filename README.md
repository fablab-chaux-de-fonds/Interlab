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