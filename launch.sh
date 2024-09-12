#!/bin/bash

git pull
PYTHON_EXEC=$(pipenv --py)
sudo "$PYTHON_EXEC" server.py