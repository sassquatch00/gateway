from  serial import Serial

ser = serial('/dev/serial/by-id', 115200, timeout=1)

while True:
    rcv = ser.readline()
    cmd = rcv.decode('utf-8').rstrip()
