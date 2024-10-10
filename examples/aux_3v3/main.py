from jng import JNG
import time

jng = JNG()

# JNG header present at the bottom of the board has a 3VA pin that can be used
# to power external devices. The 3VA pin is connected to a dedicated 3.3V voltage
# regulator that can supply up to 600mA of current.
#
# This regulator can be enabled or disabled.

# Enable 3.3V regulator
# You can use one of the following methods:
jng.enable_aux_LDO()
jng.aux_LDO_state(1)

time.sleep(1)

# Disable 3.3V regulator
# You can use one of the following methods:
jng.disable_aux_LDO()
jng.aux_LDO_state(0)