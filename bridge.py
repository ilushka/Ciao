#!/usr/bin/python -u
#ADD LICENSE
#ADD FEW LINES ABOUT PREFERRING inline communication OVER CRC

import io, os, sys, signal
import logging, json
from threading import Thread
import time
import atexit

import settings
from utils import *
from bridgeconnector import BridgeConnector
import bridgeserver

#function to handle OS signals
def signal_handler(signum, frame):
	global logger
	global keepcycle
	logger.debug("Received signal %d" % signum)
	keepcycle = False

#opening logfile
logging.basicConfig(filename=settings.conf['logfile'], level=logging.DEBUG)
logger = logging.getLogger("bridge")

#loading configuration for connectors
settings.load_connectors(logger)

#check if connectors have been actually loaded
if not "connectors" in settings.conf or len(settings.conf["connectors"]) == 0:
	logger.debug("No connector enabled, exiting.")
	sys.exit(1)

#creating shared dictionary
shd = {}

#start bridgeserver (to interact with connectors)
server = Thread(name="server", target=bridgeserver.init, args=(settings.conf,shd,))
server.daemon = True
server.start()

#we start connectors after bridgeserver (so they can register themselves on init_conf)
for connector, connector_conf in settings.conf['connectors'].items():
	shd[connector] = BridgeConnector(connector, connector_conf)

#TODO
# would be great to start another thread to control bridge status

if settings.debug:
	print "Starting bridge in DEBUG MODE"
	logger.debug("Starting bridge in DEBUG MODE")

	handle = io.open(settings.basepath + "fake.stdin", "r+b")
else:
	#disable echo on terminal 
	enable_echo(sys.stdin, False)

	#allow terminal echo to be enabled back when bridge exits
	atexit.register(enable_echo, sys.stdin.fileno(), True)
	handle = io.open(sys.stdin.fileno(), "rb")

#variable for controlling while loop
keepcycle = True

#adding signals management
signal.signal(signal.SIGINT, signal_handler) #ctrl+c
signal.signal(signal.SIGHUP, signal_handler) #SIGHUP - 1
signal.signal(signal.SIGTERM, signal_handler) #SIGTERM - 15

while keepcycle:
	try:
		#reading from input device
		cmd = clean_command(handle.readline())
	except KeyboardInterrupt, e:
		logger.debug("SIGINT received")
	else:
		if cmd:
			logger.debug("%s" % cmd)
			connector, action = is_valid_command(cmd)
			if connector == False:
				logger.debug("unknown command: %s" % cmd)
			elif not connector in settings.conf['connectors']:
				logger.debug("unknown connector: %s" % cmd)
			else:
				shd[connector].run(action, cmd)
		# the sleep is really useful to prevent bridge to cap all CPU
		# this could be increased/decreased (keep an eye on CPU usage)
		time.sleep(0.01)

#stopping connectors (managed)
for name, connector in shd.items():
	logger.debug("Sending stop signal to %s" % name)
	connector.stop()

logger.debug("Exiting")
sys.exit(0)