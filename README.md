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

## Generate translation file

### Update PO file with new keys
```shell
docker exec -it interlab_web_1 django-admin makemessages -l fr -e html,txt
```

### Regenerate translation compiled messages
```shell
docker exec -it interlab_web_1 django-admin compilemessages
```

