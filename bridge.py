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
	global keepcycling
	logger.info("Received signal %d" % signum)
	keepcycling = False

#opening logfile
logging.basicConfig(filename=settings.conf['logfile'], level=logging.DEBUG, format=settings.conf['logformat'])
logger = logging.getLogger("bridge")

#loading configuration for connectors
settings.load_connectors(logger)

#check if connectors have been actually loaded
if not "connectors" in settings.conf or len(settings.conf["connectors"]) == 0:
	logger.critical("No connector enabled, exiting.")
	sys.exit(1)

#creating shared dictionary
shd = {}

#start bridgeserver (to interact with connectors)
server = Thread(name="server", target=bridgeserver.init, args=(settings.conf,shd,))
server.daemon = True
server.start()

#we start connectors after bridgeserver (so they can register themselves)
for connector, connector_conf in settings.conf['connectors'].items():
	shd[connector] = BridgeConnector(connector, connector_conf)

	# connector must start after it has been added to shd,
	# it can register on if listed in shd
	shd[connector].start()

#TODO
# would be great to start another thread to control bridge status

#variable to "mantain control" over while loop
keepcycling = True

#adding signals management
signal.signal(signal.SIGINT, signal_handler) #ctrl+c
signal.signal(signal.SIGHUP, signal_handler) #SIGHUP - 1
signal.signal(signal.SIGTERM, signal_handler) #SIGTERM - 15

#acquiring stream for receiving/sending command from MCU
if settings.use_fakestdin:
	print "Starting bridge in DEBUG MODE"
	logger.debug("Starting bridge in DEBUG MODE")

	handle = io.open(settings.basepath + "fake.stdin", "r+b")
else:
	#disable echo on terminal 
	enable_echo(sys.stdin, False)

	#allow terminal echo to be enabled back when bridge exits
	atexit.register(enable_echo, sys.stdin.fileno(), True)
	handle = io.open(sys.stdin.fileno(), "rb")
	flush_terminal(sys.stdin)

while keepcycling:
	try:
		#reading from input device
		cmd = clean_command(handle.readline())
	except KeyboardInterrupt, e:
		logger.warning("SIGINT received")
	except IOError, e:
		logger.warning("Interrupted system call")
	else:
		if cmd:
			logger.debug("%s" % cmd)
			connector, action = is_valid_command(cmd)
			if connector == False:
				logger.warning("unknown command: %s" % cmd)
			elif not connector in settings.conf['connectors']:
				logger.warning("unknown connector: %s" % cmd)
			else:
				shd[connector].run(action, cmd)

		# the sleep is really useful to prevent bridge to cap all CPU
		# this could be increased/decreased (keep an eye on CPU usage)
		time.sleep(0.01)

#stopping connectors (managed)
for name, connector in shd.items():
	logger.info("Sending stop signal to %s" % name)
	connector.stop()

logger.info("Exiting")
sys.exit(0)