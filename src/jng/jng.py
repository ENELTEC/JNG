import os
import gc
from machine import Pin, I2C, SPI, UART, ADC

from ._pinout import JNG_E_V1_R1

class ETH:
    def __init__(self, spi, rst, int, cs):
        self.spi = spi
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.int = Pin(int, Pin.IN)
        self.cs = Pin(cs, Pin.OUT, value=1)

class JNG:
    def __init__(self, pinout:dict=JNG_E_V1_R1) -> None:
        self._pinout = pinout
        
        self.led1 = Pin(pinout['LED1'], Pin.OUT, value=0)
        self.led2 = Pin(pinout['LED2'], Pin.OUT, value=0)
        
        self.aux = Pin(pinout['AUX'], Pin.OUT, value=0)
        
        self._vbat = ADC(Pin(pinout['VBAT']))
        self._vbat.atten(ADC.ATTN_11DB)
        
        self._vusb = ADC(Pin(pinout['VUSB']))
        self._vusb.atten(ADC.ATTN_11DB)
        
        self.i2c = I2C(0, sda=Pin(pinout['I2C']['sda']), scl=Pin(pinout['I2C']['scl']))
        self.uart = UART(1, tx=Pin(pinout['UART']['tx']), rx=Pin(pinout['UART']['rx']), baudrate=115200)
    
        self._sd_detect = Pin(pinout['SD']['detect'], Pin.IN, Pin.PULL_UP)
        
        self.boot_sw = Pin(0, Pin.IN)

    def uart_baudrate(self, baudrate:int) -> None:
        self.uart.init(baudrate=baudrate)
    
    def flip_uart_pins(self) -> None:
        self.uart.deinit()
        self.uart = UART(1, tx=Pin(self._pinout['UART']['rx']), rx=Pin(self._pinout['UART']['tx']), baudrate=115200)
    
    def flip_i2c_pins(self) -> None:
        #self.i2c.deinit()
        self.i2c = I2C(sda=Pin(self._pinout['I2C']['scl']), scl=Pin(self._pinout['I2C']['sda']))
    
    @property
    def vbat(self) -> float:
        return self._vbat.read() * self._pinout['VBAT_GAIN']
    
    @property
    def vusb(self) -> float:
        return self._vusb.read() * self._pinout['VUSB_GAIN']
    
    @property
    def sd_card_present(self) -> bool:
        return not self._sd_detect.value()