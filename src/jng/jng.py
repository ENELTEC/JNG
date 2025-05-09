import os
import gc
import ubinascii
from machine import Pin, I2C, SPI, UART, ADC
from machine import unique_id, RTC
import network
from time import time, sleep, ticks_ms, mktime

from ._pinout import JNG_E_V1_R1, JNG_E_V1_R2

from .peripherals.sdcard import SDCard
from .peripherals.pcf8563 import PCF8563
from .peripherals.urtc import DS1307

from .utils.zfill import zfill
from .utils.NTPlib import NTP_time

def _foo(pin):
    pass

class JNG:
    def __init__(self, pinout:dict=JNG_E_V1_R2, verbose:bool = False) -> None:
        self._START_TIME = time()
        self._pinout = pinout
        self._verb = verbose
        self._sd_mounting_point = '/sd'
        
        self._vbat = ADC(Pin(pinout['VBAT']))
        self._vbat.atten(ADC.ATTN_11DB)
        
        self._vusb = ADC(Pin(pinout['VUSB']))
        self._vusb.atten(ADC.ATTN_11DB)

        self._sd_detect = Pin(pinout['SD']['detect'], Pin.IN, Pin.PULL_UP)

        self._i2c_irq = Pin(pinout['I2C']['irq'], Pin.IN) # On board 4k7 pull-up resistor
        self._i2c_irq.irq(trigger=Pin.IRQ_FALLING, handler=self._i2c_irq)
        self.i2c_irq_handler = None
        
        self.UNIQUE_ID = ubinascii.hexlify(unique_id())
        self.RAW_UNIQUE_ID = unique_id()
        self.RTC = RTC()
        
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
            try:
                self.instance_sd_card()
                os.mount(self.sdcard, self._sd_mounting_point)
            except Exception as e:
                print("SD card mount error: ", e)
                self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)
        else:
            self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)
        
        _i2c_addr = self.i2c.scan()
        if 81 in _i2c_addr:
            self.hwrtc = PCF8563(self.i2c)
        elif 104 in _i2c_addr:
            self.hwrtc = DS1307(self.i2c)
        else:
            self.hwrtc = None

    def _i2c_irq(self, pin) -> None:
        if self.i2c_irq_handler is not None:
            if callable(self.i2c_irq_handler):
                self.i2c_irq_handler(pin)

    def _sd_detect_handler(self, pin) -> None:
        # disable interrupt to prevent multiple calls
        self._sd_detect.irq(trigger=Pin.IRQ_RISING, handler=_foo)
        sleep(0.1)
        if self.sd_card_present:
            self.instance_sd_card()
            os.mount(self.sdcard, self._sd_mounting_point)
        else:
            self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)

    def _VERB(self, *args, **kwargs):
        if self._verb: print(*args, **kwargs)

    def uart_baudrate(self, baudrate:int) -> None:
        self.uart.init(baudrate=baudrate)
    
    def invert_uart(self) -> None:
        self.uart.deinit()
        self.uart = UART(1, tx=Pin(self._pinout['UART']['rx']), rx=Pin(self._pinout['UART']['tx']), baudrate=115200)
    
    def invert_i2c(self) -> None:
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
    
    def instance_sd_card(self) -> SDCard:
        self.sdcard = SDCard(self.spi, Pin(self._pinout['SD']['cs']) )
        return self.sdcard
    
    def umount_sd_card(self) -> None:
        os.umount(self._sd_mounting_point)
        self._sd_detect.irq(trigger=Pin.IRQ_FALLING, handler=self._sd_detect_handler)
        gc.collect()
    
    def instance_nic(self):
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
    
    def get_firmware_version(self):
        return os.uname()[2]
    
    def get_time_unix(self):
        return time() + 946684800

    def get_uptime(self):
        return time() - self._START_TIME

    def get_uniqueid(self):
        return self.UNIQUE_ID
    
    def get_raw_uniqueid(self):
        return self.RAW_UNIQUE_ID
    
    def pw_status(self) -> str:
        if self.vusb < self.vbat:
            return ("DISCONECTED")
        else:
            if self.vbat < 4.2:
                return ("CHARGING")
            else:
                return ("CONNECTED")
    
    def enable_aux_LDO(self):
        self.aux_LDO_state(1)
    
    def disable_aux_LDO(self):
        self.aux_LDO_state(0)
    
    def aux_LDO_state(self, *args):
        return self.aux.value( *args )
    
    def datetime(self):
        return(self.RTC.datetime())
    
    def timestamp(self, datetime = None):
        if datetime is None:
            datetime = self.datetime()
            return mktime((datetime[0], datetime[1], datetime[2], datetime[4], datetime[5], datetime[6], datetime[3], 0)) + 946684800
        else:
            return time() + 946684800
    def datetimeIsoformat(self, datetime=None):
        if datetime is None:
            datetime = self.datetime()
        return str(datetime[0]) + '-' + zfill(str(datetime[1]),2) + '-' + zfill(str(datetime[2]),2) + 'T' + zfill(str(datetime[4]),2) + ':' + zfill(str(datetime[5]),2) + ':' + zfill(str(datetime[6]),2) + '.' + str(datetime[7])

    def ntp_update(self, host, timezone, timeout=None, update_hrtc=True):
        ntp = NTP_time(host, timezone, 1)
        uptime_old = self.get_uptime()
        x = ticks_ms()
        _timeout_hold = ntp._timeout
        try:
            if timeout is not None:
                ntp._timeout = timeout
            ntp.settime()
            if update_hrtc and hasattr(self, "hwrtc"):
                if hasattr(self.hwrtc, 'write_now'): self.hwrtc.write_now() #self.hwrtc.datetime(self.RTC.datetime())
                else: self.hwrtc.datetime(self.RTC.datetime())
        except Exception as e:
            print("NTP error: ", e)
            if hasattr(self, "hwrtc"):
                datetime = self.hwrtc.datetime()
                ntp.settime((
                    datetime.year,
                    datetime.month,
                    datetime.day,
                    datetime.hour - timezone, ## this is the method
                    datetime.minute,
                    datetime.second,
                    0,
                    datetime.weekday
                ))
                print("Sync with external RTC!")
        finally:
            ntp._timeout = _timeout_hold
        y = ticks_ms()

        self._START_TIME = time() - uptime_old - int((y - x)/1000)
        return True