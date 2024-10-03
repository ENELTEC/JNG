import os
import gc
import time
from machine import Pin, I2C, SPI, UART, ADC
import network

from ._pinout import JNG_E_V1_R1

from .peripherals.sdcard import SDCard
from .peripherals.pcf8563 import PCF8563

def _foo(pin):
    pass

class JNG:
    def __init__(self, pinout:dict=JNG_E_V1_R1, verbose:bool = False) -> None:
        self._pinout = pinout
        self._verb = verbose
        self._sd_mounting_point = '/sd'
        
        self._vbat = ADC(Pin(pinout['VBAT']))
        self._vbat.atten(ADC.ATTN_11DB)
        
        self._vusb = ADC(Pin(pinout['VUSB']))
        self._vusb.atten(ADC.ATTN_11DB)

        self._sd_detect = Pin(pinout['SD']['detect'], Pin.IN, Pin.PULL_UP)
        
        self.led1 = Pin(pinout['LED1'], Pin.OUT, value=0)
        self.led2 = Pin(pinout['LED2'], Pin.OUT, value=0)
        
        self.aux = Pin(pinout['AUX'], Pin.OUT, value=0)
        
        self.i2c = I2C(0, sda=Pin(pinout['I2C']['sda']), scl=Pin(pinout['I2C']['scl']))
        self.uart = UART(1, tx=Pin(pinout['UART']['tx']), rx=Pin(pinout['UART']['rx']), baudrate=115_200)
        self.spi = SPI(1, baudrate = 10000000, 
            polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
            sck = Pin(pinout['SPI']['sck'], Pin.OUT, Pin.PULL_DOWN), 
            mosi = Pin(pinout['SPI']['mosi'], Pin.OUT, Pin.PULL_UP), 
            miso = Pin(pinout['SPI']['miso'], Pin.IN, Pin.PULL_UP)
        )
        
        self.boot_sw = Pin(0, Pin.IN)
        
        self.sdcard = None
        if self.sd_card_present:
            self.intance_sd_card()
            os.mount(self.sdcard, self._sd_mounting_point)
        else:
            self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)
        
        _i2c_addr = self.i2c.scan()
        if 81 in _i2c_addr:
            self.hwrtc = PCF8563(self.i2c)
        else:
            self.hwrtc = None

    def _sd_detect_handler(self, pin) -> None:
        # disable interrupt to prevent multiple calls
        self._sd_detect.irq(trigger=Pin.IRQ_RISING, handler=_foo)
        time.sleep(0.1)
        if self.sd_card_present:
            self.intance_sd_card()
            os.mount(self.sdcard, self._sd_mounting_point)
        else:
            self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)

    def _VERB(self, *args, **kwargs):
        if self._verb: print(*args, **kwargs)

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
    
    def intance_sd_card(self) -> SDCard:
        self.sdcard = SDCard(self.spi, Pin(self._pinout['SD']['cs']) )
        return self.sdcard
    
    def umount_sd_card(self) -> None:
        os.umount(self._sd_mounting_point)
        self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)
        gc.collect()
    
    def intance_nic(self):
        #self.rst = Pin(self._pinout['ETH']['rst'], Pin.OUT, value=1)
        # self.int = Pin(self._pinout['ETH']['int'], Pin.IN)
        # self.cs = Pin(self._pinout['ETH']['cs'], Pin.OUT, value=1)
        
        return network.LAN(
            phy_type=network.PHY_W5500, 
            spi=self.spi, 
            phy_addr=1, 
            cs=Pin(self._pinout['ETH']['cs'], Pin.OUT), 
            int=Pin(self._pinout['ETH']['int'])
        )