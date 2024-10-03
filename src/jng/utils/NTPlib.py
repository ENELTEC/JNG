try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct
from machine import RTC
import utime

class NTP_time:

    def __init__(self, HOST = 'a.ntp.br', FUSO = -3, timeout = 1):
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        self.NTP_DELTA = 3155673600

        self.host = HOST
        self.fuso = FUSO
        self._timeout = timeout

    def ntp_time(self):
        return self.time()

    def time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1b

        addr = socket.getaddrinfo(self.host, 123)[0][-1]

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self._timeout)

        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        x = val - self.NTP_DELTA
        return (x)

    def datetime(self, timestamp=None):
        if timestamp is None: timestamp = self.time()
        return utime.localtime(timestamp)

# There's currently no timezone support in MicroPython, so
# utime.localtime() will return UTC time (as if it was .gmtime())
    def ntp_settime(self):
        return self.settime()

    def settime(self, datetime = None): ## (year, month, day, hour, minute, second, milli, weekday)
        if datetime is None: datetime = self.datetime()

        year = datetime[0]
        month = datetime[1]
        day = datetime[2]
        weekday = datetime[7]
        hour = datetime[3] + self.fuso
        minute = datetime[4]
        second = datetime[5]
        millisecond = 0
    
        RTC().datetime((year, month, day, weekday, hour, minute, second, millisecond))
        return(True)
