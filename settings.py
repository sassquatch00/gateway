# -*- coding: utf-8 -*-

import logging

GATEWAY = {
    # "name" : "Terminal",
    "name" : "Terminal",
    "heartbeat_interval_s" : 60
}


LOGGING = {
    "format" : "%(asctime)s %(levelname)s %(filename)s:%(funcName)s():%(lineno)i: %(message)s",
    "datefmt" : "%Y-%m-%d %H:%M:%S",
    "level" : logging.DEBUG,
}


MQTT = {
    "broker" : "broker.mqttdashboard.com",

    # Topics to publish to for various types of data
    "topics" : {
        "sensors"   : f"{GATEWAY['name']}/sensors",
        "control"   : f"{GATEWAY['name']}/control",
        "heartbeat" : f"{GATEWAY['name']}/heartbeat",
    }
}


DWEETIO = {
    "thing_name" : f"{GATEWAY['name']}"
}
