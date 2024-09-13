
TABLE_SIZE = 60
NUMB_TABLES = 18
MAIN_COLOR = (199,21,133)

TABLE_STRIP_PIN = 18   # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0)
TABLE_BRIGHTNESS = 255 # Set to 0 for darkest and 255 for brightest

PIXEL_MAX_CURRENT = 0.006 # 6mA
TABLE_MAX_CURRENT = 1 # 1A

#### Slave conf
IS_SLAVE = True
SLAVE_BASE_URL = None

#### Master conf
IS_SLAVE = False
SLAVE_BASE_URL = "http://192.168.1.26/"
MASTER_NUMB_TABLES = 10
