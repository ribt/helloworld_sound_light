import yaml
from time import sleep, time
from random import randint
import flask
from rpi_ws281x import PixelStrip, Color
from enum import Enum
from constants import *
from threading import Thread

MAIN_COLOR = Color(*MAIN_COLOR)
TOTAL_PIXELS = NUMB_TABLES * TABLE_SIZE

class Animation(Enum):
    IDLE = 1
    FLAG = 2
    PWNED = 3

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

def decreaseBrightness(color, coefficient):
    assert coefficient >= 0 and coefficient <= 1
    r = int(color.r * coefficient)
    g = int(color.g * coefficient)
    b = int(color.b * coefficient)
    return Color(r, g, b)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(colors=[wheel(i) for i in range(256)]):
    colors.insert(0, colors.pop())
    step = max(256 // TABLE_SIZE, 1)
    return [colors[(i*step)%256] for i in range(TABLE_SIZE)]

def flag_anim(tick):
    if tick >= TABLE_SIZE * 5:
        return None
    pixels = [Color(0, 255, 0) for _ in range(tick//5)] + [Color(0, 0, 0) for _ in range(TABLE_SIZE - tick//5)]
    return pixels

def computeTablePixels(state: TableState, reverse=False):
    ret = None
    if state.getAnimation() == Animation.FLAG:
        ret = flag_anim(state.getTick())
        state.tick()
    elif state.getAnimation() == Animation.PWNED:
        ret = rainbow()
    if reverse and ret is not None:
        ret = ret[::-1]
    return ret

def adaptBrightnessToMaxCurrent(pixels):
    for table in range(NUMB_TABLES):
        estimated_current = 0
        tablePixels = pixels[table*TABLE_SIZE:(table+1)*TABLE_SIZE]
        for pixel in tablePixels:
            estimated_current += (pixel.r + pixel.g + pixel.b) / (255*3) * PIXEL_MAX_CURRENT * LED_BRIGHTNESS/255
        if estimated_current > TABLE_MAX_CURRENT:
            ratio = TABLE_MAX_CURRENT / estimated_current
            for i in range(len(tablePixels)):
                pixels[table*TABLE_SIZE+i] = decreaseBrightness(tablePixels[i], ratio)

# arguments are lists to keep state between calls
def idleAnimation(tick=[0], coefficients=[randint(1, 100)/100 for _ in range(TOTAL_PIXELS)]):
    if tick[0] % 10 == 0:
        tick[0] = 0
        coefficients.insert(0, coefficients.pop())
    for i in range(len(coefficients)):
        coefficients[i] = coefficients[i] + randint(-50, 50)/1000
        coefficients[i] = max(0.3, min(0.9, coefficients[i]))
    pixels = [decreaseBrightness(MAIN_COLOR, coefficient) for coefficient in coefficients]
    tick[0] += 1
    return pixels

def animateTables(pixels):
    for table in range(NUMB_TABLES):
        if table_states[table].getAnimation() == Animation.IDLE:
            continue
        tablePixels = computeTablePixels(table_states[table], reverse=(table%2==1))
        if tablePixels is None:
            table_states[table] = TableState(Animation.IDLE)
            continue
        for i in range(TABLE_SIZE):
            pixels[table*TABLE_SIZE+i] = tablePixels[i]

def showPixels(strip, pixels):
    adaptBrightnessToMaxCurrent(pixels)
    for i in range(TOTAL_PIXELS):
        strip.setPixelColor(i, pixels[i])
    strip.show()

def stripControl():
    global forcedColor
    strip = PixelStrip(TOTAL_PIXELS, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    while True:
        if forcedColor is not None:
            if forcedEndTime is not None and time() > forcedEndTime:
                forcedColor = None
                continue
            pixels = [forcedColor for _ in range(TOTAL_PIXELS)]
            showPixels(strip, pixels)
        else:
            if roundEndTime is not None and time() > roundEndTime:
                continue
            pixels = idleAnimation()
            animateTables(pixels)
            showPixels(strip, pixels)
        sleep(0.01)

app = flask.Flask(__name__)

def reprColor(c):
    return "#{:02x}{:02x}{:02x}".format(c.r, c.g, c.b)

@app.route('/status', methods=['GET'])
def status():
    rep = {}
    rep["config"] = {"tableSize": TABLE_SIZE, "numbTables": NUMB_TABLES, "ledBrightness": LED_BRIGHTNESS, "tableMaxCurrent": TABLE_MAX_CURRENT}
    if forcedColor is None:
        rep["forced"] = None
    else:
        rep["forced"] = {"color": reprColor(forcedColor), "remainingForcedTime": max(0, forcedEndTime - time()) if forcedEndTime is not None else None}
    rep["tables"] = [state.getAnimation().name for state in table_states]
    rep["remainingRoundTime"] = max(0, roundEndTime - time()) if roundEndTime is not None else None
    return flask.jsonify(rep)

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
    table_states[body["table"]] = TableState(Animation.PWNED)
    return 'OK'

@app.route('/round', methods=['POST'])
def round():
    global table_states, roundEndTime, forcedColor
    body = flask.request.get_json()
    if "duration" in body:
        roundEndTime = time() + body["duration"]*60
    else:
        roundEndTime = None
    table_states = [TableState(Animation.IDLE) for _ in range(NUMB_TABLES)]
    forcedColor = None
    return 'OK'

@app.route('/forceColor', methods=['POST'])
def forceColor():
    global forcedColor, forcedEndTime
    body = flask.request.get_json()
    forcedColor = Color(int(body["color"][1:3], 16), int(body["color"][3:5], 16), int(body["color"][5:7], 16))
    if "duration" in body:
        forcedEndTime = time() + body["duration"]*60
    else:
        forcedEndTime = None
    return 'OK'

if __name__ == '__main__':
    table_states = [TableState(Animation.IDLE) for _ in range(NUMB_TABLES)]
    roundEndTime = None
    forcedColor, forcedEndTime = None, None

    thread = Thread(target=stripControl)
    thread.start()
    app.run(debug=False, host='0.0.0.0', port=80)
