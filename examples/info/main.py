from jng import JNG

jng = JNG()

print("MicroPython version: ", jng.get_firmware_version())
print("ESP32 Unique ID:     ", jng.get_uniqueid())
print("JNG uptime:          ", jng.get_uptime())
print("Power status:        ", jng.pw_status())