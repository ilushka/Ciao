#!/usr/bin/python
##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import os, sys, signal
import json, logging
from Queue import Queue
import time

from xmppciao import XMPPCiao
from xmppclient import XMPPClient

# function to handle SIGHUP/SIGTERM
def signal_handler(signum, frame):
	global logger
	logger.info("SIGNAL CATCHED %d" % signum)
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
		runfile = open("/var/run/xmpp-ciao.pid", "w")
		runfile.write("%d" % pid)
		runfile.close()
		sys.exit(0)

except OSError, e:
	logger.critical("Fork failed")
	sys.exit(1)

xmpp_queue = Queue()
socket_queue = Queue()

try:
	xmpp = XMPPClient(shd["conf"]["params"], socket_queue)
except Exception, e:
	logger.critical("Exception while creating XMPPClient: %s" % e)
	sys.exit(1)

signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore SIGINT(ctrl+c)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if xmpp.connect():
	logger.info("Connected to %s" % xmpp.host)
	
	shd["requests"] = {}

	ciaoclient = XMPPCiao(shd, xmpp_queue, socket_queue)
	ciaoclient.start()

	# endless loop until SIGHUP/SIGTERM
	while shd["loop"] :
		if not xmpp_queue.empty():
			entry = xmpp_queue.get()
			logger.debug("Entry %s" % entry)

			# if entry received from ciao is a "response"
			if entry['type'] == "response":
				original_checksum = entry["source_checksum"]
				if not original_checksum in shd["requests"]:
					logger.warning("Received response to unknown checksum %s" % original_checksum)
					continue
				original_message = shd["requests"][original_checksum]
				to = str(original_message['data'][0])
				message = str(entry['data'][0])
			# else if entry received from ciao is an "out" message
			elif entry['type'] == "out":
				to = str(entry['data'][0])
				message = str(entry['data'][1])
			else:
				continue
			
			xmpp.send_message(mto=to, mbody=message, mtype='chat')

		# the sleep is really useful to prevent ciao to cap all CPU
		# this could be increased/decreased (keep an eye on CPU usage)
		# time.sleep is MANDATORY to make signal handlers work (they are synchronous in python)
		time.sleep(0.01)

	xmpp.disconnect(wait=True)
	logger.info("XMPP connector is closing")
	sys.exit(0)

else:
	logger.critical("Unable to connect to %s" % params["host"])