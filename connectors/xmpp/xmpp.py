##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import os, sys, signal
import asyncore, json
from threading import Thread, Event
from Queue import Queue
import logging

import async_socket
from xmpp_client import XMPP_Client

def signal_handler(signum, frame):
    file=open("log.txt","a")
    file.write("SIGNAL CATCHED\n")
    file.close()
    global loop
    loop = False

def child_main(shd, xmpp_queue, socket_queue):
    socket = async_socket.BridgeSocket(shd, xmpp_queue, socket_queue)
    socket.handle_connect("127.0.0.1", 8900)
    params = {
        "action" : "register",
        "name" : "xmpp"
    }
    socket.send(json.dumps(params))
    asyncore.loop(0.1)

#shared
shd = {}

#read configuration
json_conf = open("xmpp.json.conf").read()
shd["conf"] = json.loads(json_conf)

#init log
logging.basicConfig(filename="xmpp.log", level=logging.DEBUG)
logger = logging.getLogger("xmpp")

params = shd["conf"]["params"]

xmpp_user = params["username"]
xmpp_password = params["password"]

if "domain" in params:
    xmpp_user += "@" + params["domain"]
else:
    xmpp_user += "@" + params["host"]

try:
    pid = os.fork()
    print pid
    if pid > 0:
        # Exit parent process
        sys.exit(0)
except OSError, e:
    self.logger("Fork failed")
    sys.exit(1)

loop=True

xmpp_queue = Queue()
socket_queue = Queue()

xmpp = XMPP_Client(xmpp_user, xmpp_password, socket_queue)

# Service Discovery
xmpp.register_plugin('xep_0030')
# Data Forms
xmpp.register_plugin('xep_0004')
# PubSub
xmpp.register_plugin('xep_0060')
# XMPP Ping
xmpp.register_plugin('xep_0199')

signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if xmpp.connect((params["host"], params["port"]), use_tls = params["tls"], use_ssl = params["ssl"]):
    xmpp.process(block=False)
    logger.debug("Connected to %s" % params["host"])
    
    shd["requests"] = {}

    child = Thread(target = child_main, args=(shd, xmpp_queue, socket_queue))
    child.daemon = True
    child.start()

    while loop :
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

    child.exit()
    sys.exit(0)

else:
    logger.debug("Unable to connect to %s" % params["host"])