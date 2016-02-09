#!/usr/bin/python
###
# This file is part of Arduino Ciao
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# Copyright 2015 Arduino Srl (http://www.arduino.org/)
# 
# authors:
# _giuseppe[at]arduino[dot]org
#
###

import os, sys, signal
import json, logging
from Queue import Queue
import time

from mqttciao import MQTTCiao
from mqttclient import MQTTClient
import paho.mqtt.client as mqtt
import ciaotools

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

#read configuration
# TODO: verify configuration is a valid JSON
json_conf = open(shd["basepath"]+"mqtt.json.conf").read()
shd["conf"] = json.loads(json_conf)

#init log
logger = ciaotools.get_logger("mqtt", logconf=shd["conf"], logdir=shd["basepath"])

#forking to make process standalone
try:
	pid = os.fork()
	if pid > 0:
		# Save child PID to file and exit parent process
		runfile = open("/var/run/mqtt-ciao.pid", "w")
		runfile.write("%d" % pid)
		runfile.close()
		sys.exit(0)

except OSError, e:
	logger.critical("Fork failed")
	sys.exit(1)

mqtt_queue = Queue()
ciao_queue = Queue()

try:
	mqttclient = MQTTClient(shd["conf"]["params"], ciao_queue)
except Exception, e:
	logger.critical("Exception while creating MQTTClient: %s" % e)
	sys.exit(1)

signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore SIGINT(ctrl+c)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if mqttclient.connect():
	logger.info("Connected to %s" % shd['conf']['params']['host'])
	
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
	logger.critical("Unable to connect to %s" % shd["conf"]["params"]["host"])