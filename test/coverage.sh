#!/bin/sh

# Perform unit tests coverage
coverage run --data-file=test/.coverage --source='/code' manage.py test

# Generate HTML converage report
coverage html --data-file=test/.coverage --directory test/html

# Generate coverage badge SVG
cd test
coverage-badge -o html/coverage.svg 

# Must remove gitignore in order to be able to commit gh-pages
rm html/.gitignore