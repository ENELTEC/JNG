from jng import JNG
from time import sleep

jng = JNG()

# W5500 Ethernet Controller has no internal MAC address, so we need to set it manually

nic = None
def connect_nic(mac=b'\xde\xad\xbe\xef\xfe\xed'):
    global nic
    nic = jng.instance_nic() ## initialize w5500 ethernet controller
    nic_mac = mac[:-1] + (mac[-1]+1).to_bytes(1, 'big')
    nic.config(mac=nic_mac)
    nic.active(1)
    _count = 0
    while not nic.isconnected():
        print('Connecting to network...')
        sleep(1)
        if _count > 15:
            print('Failed to connect to network')
            break
        _count += 1
    print(nic.ifconfig())

connect_nic()
jng.ntp_update(
    host        = 'a.ntp.br',
    timezone    = -3,
    update_hrtc = True # Update hardware RTC (Real Time Clock) with NTP time
)
# jng.ntp_update will update ESP32 internal RTC with PCF8563 RTC IC mounted on
# JNG board if NTP time is not available.