import asyncore
import socket
import os
import sys
import logging
#from multiprocessing import Process, Manager, Queue
#from multiprocessing.managers import SyncManager
from Queue import Queue
from threading import Thread
from bridgeutils import BridgeConnector
import bridgeserver

#MAIN
conf = {
	"backlog" : 5, #this value must match number of enabled connectors (we could sizeof(modules))
	"srvhost" : "localhost",
	"srvport" : 8900,
	"logfile" : "test.log",
	"modules" : ['xmpp']
}

#shared dictionary
shd = {}

"""
#TODO we should:
	- load bridge_config
	- scan SOMEDIR_CONF for connector configuration (bridge-side)
"""

#this is the connector used to interact with serial (tty)
shd['serial'] = BridgeConnector("serial", Queue())

for m in conf['modules']:
	shd[m] = BridgeConnector(m, Queue())

bridge = Thread(name="server", target=bridgeserver.init, args=(conf,shd,))
bridge.daemon = True
bridge.start()

"""
#TODO
we have to start another thread to control bridge status
"""
allowed_actions = ["w", "r", "wr"]
logger = logging.getLogger("server")

while True:
	command = sys.stdin.readline()
	command = command.rstrip()
	logger.debug("%s" % command)
	#split command in up to three elements (connector, action, command)
	params = command.split(";",2)
	for p in params:
		logger.debug("%s" % p)
	if len(params) == 3:
		bc = params[0]
		if params[0] in conf['modules']:
			action = params[1]
			if shd[bc].is_registered() and action in allowed_actions:
				if action == "r":
					if shd[bc].has_message():
						print shd[bc].get_message()
					else:
						print "0;no_message"
				elif action == "w":
					shd[bc].queue_push(params[2])
			else:
				logger.debug("required action for connector %s (not yet registered)" % params[0])
		print command
	else:
		logger.debug("too few arguments from bridge(MCU): %s" % command)
	
