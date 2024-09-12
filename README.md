# HelloWorld Sound & Light

Projet de son et lumière pour l'évènement HelloWorld de GCC

## Installation

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install git
cd
git clone https://github.com/ribt/helloworld_sound_light
cd helloworld_sound_light
chmod +x install.sh
./install.sh
```

Brancher GND et 5V du bandeau sur GND et 5V de la RPi. Brancher le fil de donnée sur le GPIO18.

## Test

```
sudo $(pipenv --py) strandtest.py
```