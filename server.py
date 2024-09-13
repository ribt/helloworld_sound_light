from time import sleep, time
from random import randint
import flask
from rpi_ws281x import PixelStrip, Color
from enum import Enum
from config import *
from threading import Thread
from queue import Queue
import os
import requests

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
            estimated_current += (pixel.r + pixel.g + pixel.b) / (255*3) * PIXEL_MAX_CURRENT * TABLE_BRIGHTNESS/255
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

def showPixels(strip, pixels, bypassCurrentCheck=False):
    if not bypassCurrentCheck:
        adaptBrightnessToMaxCurrent(pixels)
    for i in range(TOTAL_PIXELS):
        strip.setPixelColor(i, pixels[i])
    strip.show()

def tablesStripControl():
    global forcedColor
    
    tablesStrip = PixelStrip(
        TOTAL_PIXELS,   
        TABLE_STRIP_PIN,   # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
        800000,            # LED signal frequency in hertz (usually 800khz)
        10,                # DMA channel to use for generating signal (try 10)
        False,             # True to invert the signal (when using NPN transistor level shift)
        TABLE_BRIGHTNESS,  # Set to 0 for darkest and 255 for brightest
        0                  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    )
    tablesStrip.begin()

    while True:
        if forcedColor is not None:
            if forcedEndTime is not None and time() > forcedEndTime:
                forcedColor = None
                continue
            pixels = [forcedColor for _ in range(TOTAL_PIXELS)]
            showPixels(tablesStrip, pixels)
        else:
            if roundEndTime is not None and time() > roundEndTime:
                continue
            pixels = idleAnimation()
            animateTables(pixels)
            showPixels(tablesStrip, pixels)
        sleep(0.01)

def bigStripControl():   
    bigStrip = PixelStrip(
        BIGSTRIP_SIZE,   
        BIGSTRIP_PIN,      # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
        800000,            # LED signal frequency in hertz (usually 800khz)
        10,                # DMA channel to use for generating signal (try 10)
        False,             # True to invert the signal (when using NPN transistor level shift)
        255,               # Set to 0 for darkest and 255 for brightest
        0                  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    )
    bigStrip.begin()

    while True:
        if forcedColor is not None:
            if forcedEndTime is not None and time() > forcedEndTime:
                forcedColor = None
                continue
            pixels = [forcedColor for _ in range(BIGSTRIP_SIZE)]
            showPixels(bigStrip, pixels, bypassCurrentCheck=True)
        else:
            if roundEndTime is not None and time() > roundEndTime:
                continue
            if roundEndTime is not None:
                remainingPixels = min(BIGSTRIP_SIZE, int(roundEndTime - time()))
                pixels = [Color(255, 0, 0)] * (BIGSTRIP_SIZE - remainingPixels) + [Color(255, 255, 255)] * remainingPixels
                showPixels(bigStrip, pixels, bypassCurrentCheck=True)
        sleep(0.01)

def waitAndAddSoundToQueue(duration, soundFile):
    if duration < 0:
        return
    sleep(duration)
    sounds_queue.put(soundFile)

def playSoundsInQueue():
    while True:
        soundFile = "./sounds/" + sounds_queue.get()
        os.system("sudo -u pi XDG_RUNTIME_DIR=/run/user/1000 aplay " + soundFile)

app = flask.Flask(__name__)

def reprColor(c):
    return "#{:02x}{:02x}{:02x}".format(c.r, c.g, c.b)

@app.route('/status', methods=['GET'])
def status():
    rep = {}
    rep["config"] = {"tableSize": TABLE_SIZE, "numbTables": NUMB_TABLES, "ledBrightness": TABLE_BRIGHTNESS, "tableMaxCurrent": TABLE_MAX_CURRENT}
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
    if not isinstance(body["table"], int) or body["table"] < 1 or body["table"] > NUMB_TABLES:
        return "Invalid table number", 400
    if IS_MASTER:
        sounds_queue.put(f"flag.wav")
    if SLAVE_BASE_URL and body["table"] > MASTER_NUMB_TABLES:
        try: requests.post(SLAVE_BASE_URL + "flag", json={"table": body["table"] - MASTER_NUMB_TABLES})
        except: print("Warning: Slave is not reachable")
    else:
        table_states[body["table"]-1] = TableState(Animation.FLAG)
    return 'OK'

@app.route('/box', methods=['POST'])
def box_pwned():
    global table_states
    body = flask.request.get_json()
    if not isinstance(body["table"], int) or body["table"] < 1 or body["table"] > NUMB_TABLES:
        return f"Invalid table number (must be between 1 and {NUMB_TABLES})", 400
    if IS_MASTER:
        sounds_queue.put(f"team_pwn_box/{body['table']}.wav")
    if SLAVE_BASE_URL and body["table"] > MASTER_NUMB_TABLES:
        try: requests.post(SLAVE_BASE_URL + "box", json={"table": body["table"] - MASTER_NUMB_TABLES})
        except: print("Warning: Slave is not reachable")
    else:
        table_states[body["table"]-1] = TableState(Animation.PWNED)
    return 'OK'

@app.route('/round', methods=['POST'])
def round():
    global table_states, roundEndTime, forcedColor
    body = flask.request.get_json()
    if not isinstance(body["round"], int) or body["round"] < 1 or body["round"] > 4:
        return f"Invalid round number (must be between 1 and 4)", 400
    if "duration" in body:
        if not isinstance(body["duration"], int) or body["duration"] < 1:
            return f"Invalid duration (must be a positive integer)", 400
        roundEndTime = time() + body["duration"]*60
    else:
        roundEndTime = None
    table_states = [TableState(Animation.IDLE) for _ in range(NUMB_TABLES)]
    forcedColor = None
    if IS_MASTER:
        sounds_queue.put(f"rounds/{body['round']}.wav")
        Thread(target=waitAndAddSoundToQueue, args=(body["duration"]*60 - 5*60, "remaining_time/5m.wav")).start()
        Thread(target=waitAndAddSoundToQueue, args=(body["duration"]*60 - 1*60, "remaining_time/1m.wav")).start()
        Thread(target=waitAndAddSoundToQueue, args=(body["duration"]*60, "remaining_time/over.wav")).start()
    if SLAVE_BASE_URL:
        try: requests.post(SLAVE_BASE_URL + "round", json={"round": body["round"], "duration": body["duration"]})
        except: print("Warning: Slave is not reachable")
    return 'OK'

@app.route('/forceColor', methods=['POST'])
def forceColor():
    global forcedColor, forcedEndTime
    body = flask.request.get_json()
    if not isinstance(body["color"], str) or len(body["color"]) != 7 or body["color"][0] != '#' or not all(c in "0123456789ABCDEF" for c in body["color"][1:]):
        return f"Invalid color (must be a string of the form '#RRGGBB')", 400
    forcedColor = Color(int(body["color"][1:3], 16), int(body["color"][3:5], 16), int(body["color"][5:7], 16))
    if "duration" in body:
        if not isinstance(body["duration"], int) or body["duration"] < 1:
            return f"Invalid duration (must be a positive integer)", 400
        forcedEndTime = time() + body["duration"]*60
    else:
        forcedEndTime = None
    if SLAVE_BASE_URL:
        try: requests.post(SLAVE_BASE_URL + "forceColor", json={"color": body["color"], "duration": body["duration"]})
        except: print("Warning: Slave is not reachable")
    return 'OK'

if __name__ == '__main__':
    table_states = [TableState(Animation.IDLE) for _ in range(NUMB_TABLES)]
    roundEndTime = None
    forcedColor, forcedEndTime = None, None
    sounds_queue = Queue()

    Thread(target=tablesStripControl).start()
    if IS_MASTER:
        Thread(target=bigStripControl).start()
        Thread(target=playSoundsInQueue).start()

    app.run(debug=False, host='0.0.0.0', port=80)
