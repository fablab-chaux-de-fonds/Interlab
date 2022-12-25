#!/bin/sh

coverage run --data-file=test/.coverage --source='/code' manage.py test
coverage html --data-file=test/.coverage --directory test/html
