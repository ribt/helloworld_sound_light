import yaml
from time import sleep
from random import randint
import flask
from rpi_ws281x import PixelStrip, Color
from enum import Enum
from constants import *
from threading import Thread

MAIN_COLOR = Color(*MAIN_COLOR)

strip = PixelStrip(NUMB_TABLES*TABLE_SIZE, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

class Animation(Enum):
    IDLE = 1
    FLAG = 2
    ROUND = 3

table_states = [Animation.IDLE, Animation.FLAG, Animation.ROUND]

def decreaseBrigthness(color, coefficient):
    r = int(color.r * coefficient) & 255
    g = int(color.g * coefficient) & 255
    b = int(color.b * coefficient) & 255

    return Color(r, g, b)


def point_anim(tick, prevPixels):
    if tick >= TABLE_SIZE * 10:
        return None
    colors = [Color(0, 0, 0) for _ in range(TABLE_SIZE)]
    colors[tick//10] = Color(255, 0, 0)
    return colors

def range_anim(tick, prevPixels):
    if tick >= TABLE_SIZE * 20:
        return None
    colors = [Color(0, 255, 0) for _ in range(tick//20)] + [Color(0, 0, 0) for _ in range(TABLE_SIZE - tick//20)]
    return colors

def idle_anim(tick, prevPixels):
    if tick == 0:
        return [MAIN_COLOR for _ in range(TABLE_SIZE)]
    for i in range(TABLE_SIZE):
        prevCoefficient = prevPixels[i].r / MAIN_COLOR.r
        newCoefficient = prevCoefficient + randint(-500, 500)/1000
        newCoefficient = max(0.3, min(0.9, newCoefficient))
        prevPixels[i] = decreaseBrigthness(MAIN_COLOR, newCoefficient)
    if tick % 10 == 0:
        prevPixels = [prevPixels[-1]] + prevPixels[:-1]
    return prevPixels

def computePixels(tick, prevPixels, state):
    if state == Animation.IDLE:
        return idle_anim(tick, prevPixels)
    elif state == Animation.FLAG:
        return point_anim(tick, prevPixels)
    elif state == Animation.ROUND:
        return range_anim(tick, prevPixels)

def loop():
    tick = 0
    prevPixels = [Color(0, 0, 0) for _ in range(NUMB_TABLES*TABLE_SIZE)]
    while True:
        pixels = []
        for table in range(NUMB_TABLES):
            tablePixels = computePixels(tick, prevPixels[table*TABLE_SIZE:(table+1)*TABLE_SIZE], table_states[table])
            if tablePixels is None:
                table_states[table] = Animation.IDLE
                tablePixels = [MAIN_COLOR for _ in range(TABLE_SIZE)]
            pixels += tablePixels
        for i in range(len(pixels)):
            strip.setPixelColor(i, pixels[i])


        strip.show()
        sleep(0.01)
        tick += 1

# t = Thread(target=loop)
# t.start()

loop()
