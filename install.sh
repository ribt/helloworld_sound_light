#!/bin/bash

sudo apt update
sudo apt install -y pipenv

pipenv install
pipenv run pip install flask rpi-ws281x

chmod +x launch.sh

sudo ln -s /home/pi/helloworld_sound_light/lumrpi.service /etc/systemd/system/lumrpi.service

sudo systemctl daemon-reload
sudo systemctl enable lumrpi.service
sudo systemctl start lumrpi.service

echo Service created. See status with: sudo systemctl status lumrpi.service