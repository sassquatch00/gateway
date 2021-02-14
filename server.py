import socket, threading, sys

TCP_IP = '192.168.1.219' 
TCP_PORT = 5006
BUFFER_SIZE = 20 # Normally 1024, but I want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print ('Connection address:', addr)
while True:
    command = input(">")
    if command == "LISTEN":
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        print ("received data:", data)
        conn.send(data)  # echo
    elif command == "DISCONNECT":   
        conn.close()
