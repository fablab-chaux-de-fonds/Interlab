#!/bin/sh

coverage run --data-file=test/.coverage --source='/code' manage.py test
coverage xml --data-file=test/.coverage -o test/coverage.xml
