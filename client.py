import socket
import os 
import time
from datetime import datetime 
from serial import Serial 

TCP_IP = '192.168.1.219' # this IP of my pc. When I want raspberry pi 2`s as a client, I replace it with its IP '169.254.54.195'
TCP_PORT = 5005
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

nextCompassPoll = 0.0

serialDevDir='/dev/serial/by-id' # directory containing microbit device file link

if (os.path.isdir(serialDevDir)):
    serialDevices = os.listdir(serialDevDir) 

    if (len(serialDevices) > 0):

        serialDevicePath = os.path.join(serialDevDir, serialDevices[0])

        serial = Serial(port=serialDevicePath, baudrate=19200, timeout=0.2) 

        while(True):

            receivedMsg = serial.readline()
            s.send(receivedMsg)
            data = s.recv(BUFFER_SIZE)
    else:

        print('No serial devices connected') 

else:

    print(serialDevDir + ' does not exist') 

s.close()

print ("received data:", data)