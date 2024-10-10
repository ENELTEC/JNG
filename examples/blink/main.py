from jng import JNG
import time

jng = JNG()

# JNG board has two general use LEDs, LED1 and LED2 positioned on the board
# between the USB connector and RST button. Both LEDs are connected to ESP32
#
# |  D2  |   D5  |   D4   |  D3  |
# |------|-------|--------|------|
# |  PWR | LED1  |  LED2  |  BAT |
# |      | GPIO3 | GPIO45 |      |
#
# PWR: Power LED
# BAT: Battery LED (Indicates when battery is charged)

while True:
    jng.led1.value(1)
    jng.led2.value(0)
    time.sleep(1)
    jng.led1.value(0)
    jng.led2.value(1)
    time.sleep(1)