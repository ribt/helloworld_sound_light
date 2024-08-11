import yaml
import time
import flask
from rpi_ws281x import PixelStrip, Color

# load config file
with open('config.yml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)