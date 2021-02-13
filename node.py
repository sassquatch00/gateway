from microbit import *

uart.init(baudrate=9600, bits=8, parity=None, stop=1, tx=None, rx=None)
display.scroll("ready", delay=150, wait=True, loop=False, monospace=False)

while True:
    sleep(5000)
    uart.write("sound: " + str(microphone.sound_level()))