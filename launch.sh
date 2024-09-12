#!/bin/bash

git pull --force
PYTHON_EXEC=$(pipenv --py)
sudo "$PYTHON_EXEC" server.py