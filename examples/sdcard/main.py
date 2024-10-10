from jng import JNG
import os

jng = JNG()

# JNG board has a microSD card slot connected to ESP32 SPI bus. The microSD card
# is mounted on /sd directory.
#
# If the microSD card is not present, at boot time, the /sd directory will not be
# created.
#
# Once the microSD card is inserted, this will be mounted on /sd directory.

if not jng.sd_card_present:
    print("SD Card not present")
else:
    print("SD Card present")
    print("SD Card content:")
    for file in os.listdir('/sd'):
        print(file)

# You can also unmount the microSD card manually to remove it safely from the
# microSD card slot.
# jng.umount_sd_card()