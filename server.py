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

class TableState():
    def __init__(self, animation: Animation, tick=0):
        self._animation = animation
        self._tick = tick

    def tick(self):
        self._tick += 1
    
    def getAnimation(self):
        return self._animation

    def getTick(self):
        return self._tick

table_states = [TableState(Animation.IDLE) for _ in range(NUMB_TABLES)]

def decreaseBrigthness(color, coefficient):
    r = int(color.r * coefficient) & 255
    g = int(color.g * coefficient) & 255
    b = int(color.b * coefficient) & 255

    return Color(r, g, b)


def point_anim(tick):
    if tick >= TABLE_SIZE * 10:
        return None
    colors = [Color(0, 0, 0) for _ in range(TABLE_SIZE)]
    colors[tick//10] = Color(255, 0, 0)
    return colors

def range_anim(tick):
    if tick >= TABLE_SIZE * 20:
        return None
    colors = [Color(0, 255, 0) for _ in range(tick//20)] + [Color(0, 0, 0) for _ in range(TABLE_SIZE - tick//20)]
    return colors

def computePixels(state: TableState):
    ret = None
    if state.getAnimation() == Animation.FLAG:
        ret = point_anim(state.getTick())
    elif state.getAnimation() == Animation.ROUND:
        ret = range_anim(state.getTick())
    state.tick()
    return ret

def loop():
    tick = 0
    coefficients = [randint(1, 100)/100 for _ in range(strip.numPixels())]
    while True:
        # Fill pixels with idle animation
        if tick % 10 == 0:
            coefficients = [coefficients[-1]] + coefficients[:-1]
        for i in range(len(coefficients)):
            coefficients[i] = coefficients[i] + randint(-50, 50)/1000
            coefficients[i] = max(0.3, min(0.9, coefficients[i]))
        pixels = [decreaseBrigthness(MAIN_COLOR, coefficient) for coefficient in coefficients]

        # Override pixels with table animations
        for table in range(NUMB_TABLES):
            if table_states[table].getAnimation() == Animation.IDLE:
                continue
            tablePixels = computePixels(table_states[table])
            if tablePixels is None:
                table_states[table] = TableState(Animation.IDLE)
                continue
            pixels = pixels[:table*TABLE_SIZE] + tablePixels + pixels[(table+1)*TABLE_SIZE:]

        # Set pixels
        for i in range(len(pixels)):
            strip.setPixelColor(i, pixels[i])
        strip.show()

        sleep(0.01)
        tick += 1

app = flask.Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    return flask.jsonify([state.getAnimation().name for state in table_states])

@app.route('/flag', methods=['POST'])
def flag():
    global table_states
    body = flask.request.get_json()
    table_states[body["table"]] = TableState(Animation.FLAG)
    return 'OK'

@app.route('/box', methods=['POST'])
def box_pwned():
    global table_states
    body = flask.request.get_json()
    table_states[body["table"]] = TableState(Animation.ROUND)
    return 'OK'

if __name__ == '__main__':
    thread = Thread(target=loop)
    thread.start()
    app.run(debug=False, host='0.0.0.0', port=80)