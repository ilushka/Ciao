import os
import sys
import logging
import asyncore
import socket
from Queue import Queue
from threading import Thread

import bridgeutils
import bridgeserver

#MAIN
conf = {
	"backlog" : 5, #this value must match number of enabled connectors (we could sizeof(connectors))
	"srvhost" : "localhost",
	"srvport" : 8900,
	"logfile" : "bridge.log",
	"connectors" : ['xmpp']
}

#shared dictionary
shd = {}

"""
#TODO here we have to:
	- load bridge_config
	- scan SOMEDIR_CONF for connector configuration (bridge-side)
"""

#this connector could be used to interact with bridge (tty)
shd['bridge'] = bridgeutils.BridgeConnector("bridge", Queue())

for c in conf['connectors']:
	shd[c] = bridgeutils.BridgeConnector(c, Queue())

server = Thread(name="server", target=bridgeserver.init, args=(conf,shd,))
server.daemon = True
server.start()

"""
#TODO
we have to start another thread to control bridge status
"""
logger = logging.getLogger("server")

#we must add handling method for CRC communication
while True:
	#reading from tty
	cmd = sys.stdin.readline()
	#clean and validate string
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
