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
import urllib, urllib2

from phantciao import PhantCiao
import ciaotools

# function to handle SIGHUP/SIGTERM
def signal_handler(signum, frame):
	global logger
	logger.info("SIGNAL CATCHED %d" % signum)
	global shd
	shd["loop"] = False

# function to make request to Phant instance
def phant_request(url, stream, key, data):
	global logger
	#adding private key (phant) into the header of the request
	headers = { "Phant-Private-Key" : key}

	#data is a key=value string separated by ";" char
	# it's simpler than a string separated by &, like in GET request

	data_hash = {}
	for element in data.split(";"):
		if element.strip():
			(key, value) = element.strip().split("=")
			data_hash[key] = value
		else:
			logger.debug("Empty element passed to connector: ignored!")

	#turn data_hash into URL encoded string for GET request
	data = urllib.urlencode(data_hash)
	req = urllib2.Request(url+stream, data, headers)
	try:
		response = urllib2.urlopen(req)
		result = response.read()
		logger.debug("Request answer: %s" % result)
	except Exception, e:
		logger.error("Request issue: %s" % e)

#shared dictionary
shd = {}
shd["loop"] = True
shd["basepath"] = os.path.dirname(os.path.abspath(__file__)) + os.sep

#read configuration
# TODO: verify configuration is a valid JSON
json_conf = open(shd["basepath"]+"phant.json.conf").read()
shd["conf"] = json.loads(json_conf)

#init log
logger = ciaotools.get_logger("phant", logconf=shd["conf"], logdir=shd["basepath"])

#forking to make process standalone
try:
	pid = os.fork()
	if pid > 0:
		# Save child PID to file and exit parent process
		runfile = open("/var/run/phant-ciao.pid", "w")
		runfile.write("%d" % pid)
		runfile.close()
		sys.exit(0)

except OSError, e:
	logger.critical("Fork failed")
	sys.exit(1)

phant_queue = Queue()

signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore SIGINT(ctrl+c)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
	
shd["requests"] = {}
params = shd["conf"]["params"]

# we need to check if all params are set
if not "ssl" in params or params["ssl"] == False:
	base_url = "http://"
else:
	base_url = "https://"
base_url += params["host"]+":"+str(params["port"])+"/"+params["base_uri"]

ciaoclient = PhantCiao(shd, phant_queue)
ciaoclient.start()

# endless loop until SIGHUP/SIGTERM
while shd["loop"] :
	if not phant_queue.empty():
		entry = phant_queue.get()
		logger.debug("Entry %s" % entry)

		# if entry received from ciao is an "out" message
		if entry['type'] == "out":
			stream = str(entry['data'][0])
			if not stream:
				logger.warning("Missing stream param, dropping message")
				continue

			key = str(entry['data'][1])
			if not key:
				logger.warning("Missing key param, dropping message")
				continue
			logger.debug("Key: %s" % key)

			data = str(entry['data'][2])
			if not data:
				logger.warning("Missing data param, dropping message")
				continue
			logger.debug("Data: %s" % data)

			phant_request(base_url, stream, key, data)

		else:
			continue

	# the sleep is really useful to prevent ciao to cap all CPU
	# this could be increased/decreased (keep an eye on CPU usage)
	# time.sleep is MANDATORY to make signal handlers work (they are synchronous in python)
	time.sleep(0.01)

logger.info("Phant connector is closing")
sys.exit(0)

