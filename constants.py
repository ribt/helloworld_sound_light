
TABLE_SIZE = 60
NUMB_TABLES = 18
MAIN_COLOR = (199,21,133)

# LED strip configuration:
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

PIXEL_MAX_CURRENT = 0.006 # 6mA
TABLE_MAX_CURRENT = 1 # 1A

#### Slave conf
IS_SLAVE = True
SLAVE_BASE_URL = None

#### Master conf
IS_SLAVE = False
SLAVE_BASE_URL = "http://192.168.1.26/"
MASTER_NUMB_TABLES = 10