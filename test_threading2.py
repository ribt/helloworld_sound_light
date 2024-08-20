from rpi_ws281x import PixelStrip, Color
from time import sleep
from threading import Thread

# LED strip configuration:
LED_COUNT = 30        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 50  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def blink(n):
    while True:
        sleep(0.1)
        strip.setPixelColor(n, Color(255, 0, 0))
        strip.show()
        sleep(0.1)
        strip.setPixelColor(n, Color(0, 0, 0))
        strip.show()



threads = [Thread(target=blink, args=(i,)) for i in range(30)]
for t in threads:
    t.start()

