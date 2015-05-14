#ADD LICENSE
#ADD FEW LINES ABOUT PREFERRING inline communication OVER CRC communication

import os
import sys
import logging
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

#disable echo on terminal 
enable_echo(sys.stdin, False)
#allow terminal echo to be enabled back when bridge exits
atexit.register(enable_echo, sys.stdin.fileno(), True)

#we must add handling method for CRC communication
while True:
	#reading from tty
	cmd = clean_command(sys.stdin.readline())
	connector, action = is_valid_command(cmd)
	if connector == False:
		logger.debug("unknown command: %s" % cmd)
	elif not connector in settings.conf['connectors']:
		logger.debug("unknown connector: %s" % cmd)
	else:
		shd[connector].run(action, cmd)

"""
	cmd = bridgeutils.clean_command(cmd)
	params = bridgeutils.get_params(cmd, logger)
	if bridgeutils.is_valid_command(params, logger):
		bc = params[0]
		action = params[1]
		if bc in conf['connectors']:
			if shd[bc].is_registered():
				if action == "r":
					if shd[bc].has_message():
						print "1;"+shd[bc].get_message()
					else:
						print "0;no_message"
				elif action == "w":
					shd[bc].queue_push(params[2])
			else:
				logger.debug("Required action '%s' for connector %s (not yet registered)" % (action, bc))
				print "-1;not_yet_registered"
		else:
			print "-1;unknown_connector"
	else:
		logger.debug("Too few arguments from bridge(MCU): %s" % cmd)
		print "-1;wrong_params"
"""