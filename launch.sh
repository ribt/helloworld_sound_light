#!/bin/bash

git fetch

# Try to backup local changes
git branch -d backup || true
git branch backup || true

git reset --hard origin/main

PYTHON_EXEC=$(pipenv --py)
sudo "$PYTHON_EXEC" server.py