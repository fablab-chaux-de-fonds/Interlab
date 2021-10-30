#!/bin/bash
cd "$(dirname "$0")"
source ../.env

DB="db.json"

ssh -t $SSH_USER@$SSH_HOST 'sudo docker exec -it interlab_web_1 python manage.py dumpdata --exclude contenttypes > '$DB
scp -P 22 $SSH_USER@$SSH_HOST:/home/$SSH_USER/$DB ../data/$DB
docker cp ../data/$DB interlab-web-1:code/$DB
docker exec -it interlab-web-1 python manage.py loaddata $DB
