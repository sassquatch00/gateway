import settings
import requests
import serial
import csv
import os
import subprocess
import json
import re
import paho.mqtt.client as mqtt
import sys
import logging
import argparse
import getpass
import random
import urllib
import pprint
import sched
import time
import datetime
import threading
import dweepy

# Configure logging
logging.basicConfig(format=settings.LOGGING["format"], datefmt=settings.LOGGING["datefmt"], level=settings.LOGGING["level"])
logger = logging.getLogger(__name__)

mqttc = None


# Handles the case when the serial port can't be found
def handle_missing_serial_port() -> None:
    exit()


# Initializes the serial device. Tries to get the serial port that the RPI is connected to
def get_serial_dev_name() -> str:
    logger.info(f"sys.platform: {sys.platform}")
    logger.info(f"os.uname().release: {os.uname().release}")
    logger.info("")

    serial_dev_name = None
    if "microsoft" in os.uname().release.lower(): # Windows Subsystem for Linux

        # list the serial devices available
        try:
            stdout = subprocess.check_output("pwsh.exe -Command '[System.IO.Ports.SerialPort]::getportnames()'", shell = True).decode("utf-8").strip()
            if not stdout:
                handle_missing_serial_port()
        except subprocess.CalledProcessError:
            logger.error(f"Couldn't list serial ports: {e.output.decode('utf8').strip()}")
            handle_missing_serial_port()


        # guess the serial device
        stdout = stdout.splitlines()[-1]
        serial_dev_name = re.search("COM([0-9]*)", stdout)
        if serial_dev_name:
            serial_dev_name = f"/dev/ttyS{serial_dev_name.group(1)}"

    elif "linux" in sys.platform.lower(): # Linux

        # list the serial devices available
        try:
            stdout = subprocess.check_output("ls /dev/ttyACM*", stderr=subprocess.STDOUT, shell = True).decode("utf-8").strip()
            if not stdout:
                handle_missing_serial_port()
        except subprocess.CalledProcessError as e:
            logger.error(f"Couldn't list serial ports: {e.output.decode('utf8').strip()}")
            handle_missing_serial_port()

        # guess the serial device
        serial_dev_name = re.search("(/dev/ttyACM[0-9]*)", stdout)
        if serial_dev_name:
            serial_dev_name = serial_dev_name.group(1)

    elif sys.platform == "darwin": # macOS
        
        # list the serial devices available
        try:
            stdout = subprocess.check_output("ls /dev/cu.usbmodem*", stderr=subprocess.STDOUT, shell = True).decode("utf-8").strip()
            if not stdout:
                handle_missing_serial_port()
        except subprocess.CalledProcessError:
            logger.error(f"Error listing serial ports: {e.output.decode('utf8').strip()}")
            handle_missing_serial_port()

        # guess the serial device
        serial_dev_name = re.search("(/dev/cu.usbmodem[0-9]*)", stdout)
        if serial_dev_name:
            serial_dev_name = serial_dev_name.group(1)

    else:
        logger.error(f"Unknown sys.platform: {sys.platform}")
        exit()

    logger.info(f"serial_dev_name: {serial_dev_name}")
    logger.info("Serial ports available:")
    logger.info("")
    logger.info(stdout)

    if not serial_dev_name:
        handle_missing_serial_port()

    return serial_dev_name


# Callback for when the MQTT client connects
# This function is called once just after the mqtt client is connected to the server.
def handle_mqtt_connack(client, userdata, flags, rc) -> None:
    logger.debug(f"MQTT broker said: {mqtt.connack_string(rc)}")
    if rc == 0:
        client.is_connected = True

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(settings.MQTT["topics"]["control"])
    logger.info(f"Subscribed to: {settings.MQTT['topics']['control']}")
    logger.info(f"Publish something to {settings.MQTT['topics']['control']} and the messages will appear here.")


# Callback for when a message is received from the MQTT broker.
def handle_mqtt_message(client, userdata, msg) -> None:
    logger.info(f"received msg | topic: {msg.topic} | payload: {msg.payload.decode('utf8')}")


def handle_serial_data(s: serial.Serial) -> None:
    payload = s.readline().decode("utf-8").strip()

    # publish data to MQTT broker
    logger.info(f"Publish | topic: {settings.MQTT['topics']['sensors']} | payload: {payload}")
    mqttc.publish(topic=settings.MQTT["topics"]["sensors"], payload=payload, qos=0)

    # send dweet
    dweepy.dweet_for(settings.DWEETIO["thing_name"], {"data" : payload })


def loop_heartbeat() -> None:
    while True:
        logger.debug(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
        payload=f"{settings.GATEWAY['name']},datetime,{datetime.datetime.now():%Y-%m-%d %H:%M:%S}"

        # publish data to MQTT broker
        logger.info(f"Publish | topic: {settings.MQTT['topics']['heartbeat']} | payload: {payload}")
        mqttc.publish(topic=settings.MQTT['topics']['heartbeat'], payload=payload, qos=0)

        # send dweet
        dweepy.dweet_for(settings.GATEWAY["name"], {"data" : payload })

        time.sleep(settings.GATEWAY["heartbeat_interval_s"])


def main() -> None:
    global mqttc

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", type=str, help="serial device to use, e.g. /dev/ttyS1")

    args = parser.parse_args()
    args_device = args.device

    # create mqtt client
    mqttc = mqtt.Client()

    # register callbacks
    mqttc.on_connect = handle_mqtt_connack
    mqttc.on_message = handle_mqtt_message

    # connect to broker
    mqttc.is_connected = False
    mqttc.connect(settings.MQTT["broker"])
    mqttc.loop_start()
    time_to_wait_secs = 1
    while not mqttc.is_connected and time_to_wait_secs > 0:
        time.sleep(0.1)
        time_to_wait_secs -= 0.1

    if time_to_wait_secs <= 0:
        logger.error(f"Can't connect to {settings.MQTT['broker']}")
        return

    # try to get the serial device name
    if args.device:
        serial_dev_name = args.device
    else:
        serial_dev_name = get_serial_dev_name()

    # start a heartbeat thread, to send heartbeat messages periodically
    heartbeat_thread = threading.Thread(target=loop_heartbeat)
    # heartbeat_thread.daemon = True # make thread a daemon, so that it stops when main program exits
    heartbeat_thread.start()

    with serial.Serial(port=serial_dev_name, baudrate=115200, timeout=10) as s:
        # sleep to make sure serial port has been opened before doing anything else
        time.sleep(1) 

        # reset the input and output buffers in case there is leftover data
        s.reset_input_buffer()
        s.reset_output_buffer()

        # loopy loop
        while True:

            # read from the serial port
            if s.in_waiting > 0:
                handle_serial_data(s)

    mqttc.loop_stop()
    heartbeat_thread.join()

if __name__ == "__main__":
    main()