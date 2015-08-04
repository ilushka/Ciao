#!/usr/bin/python

import os, sys, signal
import json, logging
from Queue import Queue
import time

from mqttciao import MQTTCiao
from mqttclient import MQTTClient
import paho.mqtt.client as mqtt

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
logging.basicConfig(filename=shd["basepath"]+"mqtt.log", level=logging.DEBUG)
logger = logging.getLogger("mqtt")

#read configuration
# TODO: verify configuration is a valid JSON
json_conf = open(shd["basepath"]+"mqtt.json.conf").read()
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

mqtt_queue = Queue()
ciao_queue = Queue()

#TODO remove this var
params = shd["conf"]["params"]

try:
	mqttclient = MQTTClient(shd["conf"]["params"], ciao_queue)
except Exception, e:
	logger.critical("Exception while creating MQTTClient: %s" % e)
	sys.exit(1)

signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore SIGINT(ctrl+c)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if mqttclient.connect():
	#logger.info("Connected to %s" % .host)
	
	shd["requests"] = {}

	ciaoclient = MQTTCiao(shd, mqtt_queue, ciao_queue)
	ciaoclient.start()

	# endless loop until SIGHUP/SIGTERM
	while shd["loop"] :
		if not mqtt_queue.empty():
			entry = mqtt_queue.get()
			logger.debug("Entry %s" % entry)

			# if entry received from ciao is an "out" message
			if entry['type'] == "out":
				topic = str(entry['data'][0])
				message = str(entry['data'][1])
			else:
				continue

			mqttclient.publish(topic, message)

		# the sleep is really useful to prevent ciao to cap all CPU
		# this could be increased/decreased (keep an eye on CPU usage)
		# time.sleep is MANDATORY to make signal handlers work (they are synchronous in python)
		time.sleep(0.01)

	mqttclient.disconnect()
	logger.info("MQTT connector is closing")
	sys.exit(0)

else:
	logger.critical("Unable to connect to %s" % params["host"])