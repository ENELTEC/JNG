from jng import JNG
import time

jng = JNG()

# JNG board has two resistors divider connected to ESP32 ADC pins to measure
# battery and USB voltage. The resistors are connected to GPIO2 and GPIO1
# respectively.
#
# Both ADC pins are configured with attenuation of 11dB to measure voltage
# between 0 and 3.6V.
#
# The resistors values are 100k and 100k, so the voltage at ESP32 ADC pin is
# 1/2 of the battery or USB voltage.
# This voltage is multiplied by 2 to get the real battery or USB voltage.

while True:
    print("Battery Voltage: ", jng.vbat)
    print("USB Voltage:     ", jng.vusb)
    print()
    time.sleep(1)