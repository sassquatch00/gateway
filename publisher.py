import os 
import time
from datetime import datetime 
from serial import Serial 

nextCompassPoll = 0.0

serialDevDir='/dev/serial/by-id' # directory containing microbit device file link

if (os.path.isdir(serialDevDir)):
    serialDevices = os.listdir(serialDevDir) 

    if (len(serialDevices) > 0):

        serialDevicePath = os.path.join(serialDevDir, serialDevices[0])

        serial = Serial(port=serialDevicePath, baudrate=19200, timeout=0.2) 

        while(True):

            receivedMsg = serial.readline()

            print(receivedMsg.decode('ascii'))
    else:

        print('No serial devices connected') 

else:

    print(serialDevDir + ' does not exist') 