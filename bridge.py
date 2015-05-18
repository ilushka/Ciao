#!/usr/bin/python -u
#ADD LICENSE
#ADD FEW LINES ABOUT PREFERRING inline communication OVER CRC communication

import io, os, sys, logging
from Queue import Queue
from threading import Thread
import atexit

import settings
from bridgeconnector import BridgeConnector
import bridgeserver
from utils import *

#MAIN

#shared dictionary
shd = {}

#this connector could be used to interact with bridge (tty)
shd['bridge'] = BridgeConnector("bridge", {}, Queue())

for connector, connector_conf in settings.conf['connectors'].items():
	shd[connector] = BridgeConnector(connector, connector_conf, Queue())

#start bridgeserver (to interact with connectors)
server = Thread(name="server", target=bridgeserver.init, args=(settings.conf,shd,))
server.daemon = True
server.start()

"""
#TODO
we have to start another thread to control bridge status
"""
logger = logging.getLogger("server")

if settings.debug:
	handle = io.open("pippo", "r+b")
	print "Starting bridge in DEBUG MODE"
	logger.debug("Starting bridge in DEBUG MODE")
else:
	#disable echo on terminal 
	enable_echo(sys.stdin, False)
	
	#allow terminal echo to be enabled back when bridge exits
	atexit.register(enable_echo, sys.stdin.fileno(), True)
	handle = io.open(sys.stdin.fileno(), "rb")

while True:
	#reading from input device
	cmd = clean_command(handle.readline())
	if cmd:
		logger.debug("%s" % cmd)
		connector, action = is_valid_command(cmd)
		if connector == False:
			logger.debug("unknown command: %s" % cmd)
		elif not connector in settings.conf['connectors']:
			logger.debug("unknown connector: %s" % cmd)
		else:
			shd[connector].run(action, cmd)
