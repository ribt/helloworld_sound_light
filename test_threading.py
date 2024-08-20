from rpi_ws281x import PixelStrip, Color
from time import sleep
from threading import Thread

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

def half1():
    c = 0
    while True:
        sleep(0.03)
        c += 1
        c %= 15
        for i in range(15):
            if i == c:
                strip.setPixelColor(i, Color(255, 0, 0))
            else:
                strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

def half2():
    c = 0
    while True:
        sleep(0.03)
        c += 1
        c %= 15
        for i in range(15, 30):
            if i-15 == c:
                strip.setPixelColor(i, Color(0, 255, 0))
            else:
                strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

q1 = Thread(target=half1)
q2 = Thread(target=half2)
q1.start()
q2.start()
