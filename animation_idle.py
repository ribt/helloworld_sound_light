from rpi_ws281x import PixelStrip, Color
from time import sleep
from random import randint

# LED strip configuration:
LED_COUNT = 30        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 200  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

MAIN_COLOR = Color(199,21,133)

def decreaseBrigthness(color, coefficient):
    r = int(color.r * coefficient) & 255
    g = int(color.g * coefficient) & 255
    b = int(color.b * coefficient) & 255

    return Color(r, g, b)
    
coefficients = [randint(1, 100)/100 for i in range(strip.numPixels())]
c = 0
while True:
    sleep(0.01)
    c += 1
    if c == 10:
        c = 0
        coefficients = [coefficients[-1]] + coefficients[:-1]
    for i in range(len(coefficients)):
        coefficients[i] = min(coefficients[i] + randint(-50, 50)/1000, 0.9)
        coefficients[i] = max(coefficients[i], 0.3)
        strip.setPixelColor(i, decreaseBrigthness(MAIN_COLOR, coefficients[i]))
    # print(coefficients)
    # print(sum([MAIN_COLOR.r*c + MAIN_COLOR.g*c + MAIN_COLOR.b*c for c in coefficients])/255 * 0.02)
    strip.show()