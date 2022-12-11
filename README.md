# Interlab

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
$ docker exec -it interlab-web-1 python manage.py migrate
$ docker exec -it interlab-web-1 python manage.py createsuperuser
```

## Generate translation file

### Update PO file with new keys
```shell
docker exec -it interlab-web-1 django-admin makemessages -l fr -e html,txt,py
```

### Regenerate translation compiled messages
```shell
docker exec -it interlab-web-1 django-admin compilemessages
```
No need `docker compose restart` to apply modifications. 

## Use django API
```shell
docker exec -it interlab_web_1 python manage.py shell
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
Keep the instance running in order to serve assets to django when developping. 

### Production

Install dependencies and build
```shell
$ cd frontend
$ npm install
$ npm run build
$ docker exec -it interlab-web-1 python manage.py collectstatic --noinput --clear
```


#### Production docker-compose example
Note the hosted network and the volume on static files
```
version: "3.3"
   
services:
  web:
    image: registry.fablab-chaux-de-fonds.ch/flcdf/interlab
    command: python manage.py runserver 127.0.0.1:8000
    env_file:
      - .env
    volumes:
      - /var/run/postgresql/:/var/run/postgresql/
      - static:/code/static
    network_mode: "host"

volumes:
    static:
```

#### Setup nginx
Setup Nginx to serve files, when DEBUG=False runserver will not serve static files.

Create two directory www/static where you want the static files to be binded (for instance in the same directory as docker-compose)
```shell
$ mkdir -p /your/custom/path/www/static
$ chown -R www-data:www-data /your/custom/path/www/static
```

Edit nginx site config file:
```
[...]
location /static/ {
    root /your/custom/path/www;
}
[...]
```

#### BindFS with user and permissions changes
We want to access volume from the host but using different user and permission. 
This is possible to do that using BindFS

Edit /etc/fstab:
```
bindfs#/var/lib/docker/volumes/interlab_static/_data	/your/custom/path/static	fuse	force-user=www-data,perms=0000:u+rx	0	0
```

You can find the right source directory depending on docker config using docker volume ls / inspect

### After update
Don't forget to remove volume on image update
```shell
$ docker-compose down
$ docker volume rm interlab_static
$ docker-compose up -d
```

And remount BindFS after update
```shell
$ sudo mount -a
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
docker exec -i interlab_web_1 python manage.py shell < tools/fabmanager.py
```

## Generate scheduled daily check for subscription expire warning mails
```shell
docker exec -i interlab_web_1 python manage.py createtasks
```

## Launch unit and integration tests
```shell
docker exec -i interlab_web_1 python manage.py test
```
