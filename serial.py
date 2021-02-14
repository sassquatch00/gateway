from  serial import Serial

ser = serial('/dev/ttyACM0', 115200, timeout=1)

while True:
    rcv = ser.readline()
    cmd = rcv.decode('utf-8').rstrip()
