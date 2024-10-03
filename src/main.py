import network
from jng import JNG

joker = JNG()

wlan = None
def connect_wifi(ssid, passwd):
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, passwd)
    while not wlan.isconnected():
        pass
    print('network config:', wlan.ifconfig())

nic = None
def connect_eth(mac=b'\xde\xad\xbe\xef\xfe\xed'):
    global nic
    nic = joker.intance_nic()
    nic_mac = mac[:-1] + (mac[-1]+1).to_bytes(1, 'big')
    nic.config(mac=nic_mac)