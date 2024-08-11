# HelloWorld Sound & Light

Projet de son et lumière pour l'évènement HelloWorld de GCC

## Installation

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install git pipenv
cd
git clone https://github.com/ribt/helloworld_sound_light
cd helloworld_sound_light
pipenv shell
alias python3="sudo $(which python3)"
```

Brancher GND et 5V du bandeau sur GND et 5V de la RPi. Brancher le fil de donnée sur le GPIO18.

## Test

```
python3 strandtest.py
```