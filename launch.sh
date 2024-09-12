#!/bin/bash

git pull || true

PYTHON_EXEC=$(pipenv --py)
sudo "$PYTHON_EXEC" server.py
