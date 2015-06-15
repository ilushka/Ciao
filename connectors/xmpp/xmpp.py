#!/usr/bin/python
##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import os, sys, signal
import json, logging
from Queue import Queue
import time

from bridgetools import BridgeThread
from xmppclient import XMPPClient

def signal_handler(signum, frame):
    global logger
    logger.debug("SIGNAL CATCHED %d" % signum)
    global shd
    shd["loop"] = False

#shared dictionary
shd = {}
shd["loop"] = True
shd["basepath"] = os.path.dirname(os.path.abspath(__file__)) + os.sep

#init log
logging.basicConfig(filename=shd["basepath"]+"xmpp.log", level=logging.DEBUG)
logger = logging.getLogger("xmpp")

#read configuration
#TODO
# verify configuration is a valid JSON
json_conf = open(shd["basepath"]+"xmpp.json.conf").read()
shd["conf"] = json.loads(json_conf)

#forking to make process standalone
try:
    pid = os.fork()
    if pid > 0:
        # Save child pid to file and exit parent process
        runfile = open("/var/run/xmpp-bridge.pid", "w")
        runfile.write("%d" % pid)
        runfile.close()
        sys.exit(0)

except OSError, e:
    self.logger("Fork failed")
    sys.exit(1)

params = shd["conf"]["params"]

#setting up user/password (for xmpp)
xmpp_user = params["username"]
xmpp_password = params["password"]

if "domain" in params:
    xmpp_user += "@" + params["domain"]
else:
    xmpp_user += "@" + params["host"]

xmpp_queue = Queue()
socket_queue = Queue()

xmpp = XMPPClient(xmpp_user, xmpp_password, socket_queue)

signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore SIGINT(ctrl+c)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if xmpp.connect((params["host"], params["port"]), use_tls = params["tls"], use_ssl = params["ssl"]):
    xmpp.process(block=False)
    logger.debug("Connected to %s" % params["host"])
    
    shd["requests"] = {}

    bridgeclient = BridgeThread(shd, xmpp_queue, socket_queue)
    bridgeclient.start()

    while shd["loop"] :
        if not xmpp_queue.empty():
            logger.debug("something to read in xmpp_queue")
            entry = xmpp_queue.get()
            logger.debug("entry %s" % entry)
            if entry['type'] == "response":
                original_checksum = entry["source_checksum"]
                if not original_checksum in shd["requests"]:
                    logger.debug("received response to unknown checksum %s" % original_checksum)
                    continue
                original_message = shd["requests"][original_checksum]
                to = str(original_message['data'][0])
                message = str(entry['data'][0])
            elif entry['type'] == "out":
                to = str(entry['data'][0])
                message = str(entry['data'][1])
            else:
                continue
            
            xmpp.send_message(mto=to, mbody=message, mtype='chat')
        # sleep prevents python to take full CPU during while True
        time.sleep(0.01)

    xmpp.disconnect(wait=True)
    logger.debug("XMPP connector is closing")
    sys.exit(0)

else:
    logger.debug("Unable to connect to %s" % params["host"])