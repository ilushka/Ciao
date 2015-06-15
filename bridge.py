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
try:
	conf_list = os.listdir(settings.conf['paths']['conf'])
except Exception, e:
	logger.debug("Problem opening conf folder: %s" % e)
	exit(1)
else:
	settings.conf['connectors'] = {}
	for conf_file in conf_list:
		if conf_file.endswith(".json.conf"):
			try:
				conf_json = open(settings.conf['paths']['conf'] + conf_file).read()
				conf_plain = json.loads(conf_json)
				if 'name' in conf_plain:
					connector_name = conf_plain['name']
				else:
					logger.debug("Missing connector name in configuration file(%s)" % conf_file)
					connector_name = conf_file[:-len(".json.conf")]		
				if "enabled" in conf_plain and conf_plain['enabled']:
					settings.conf['connectors'][connector_name] = conf_plain
					logger.debug("Loaded configuration for %s connector" % connector_name)
				else:
					logger.debug("Ignoring %s configuration: connector not enabled" % connector_name)
			except Exception, e:
				logger.debug("Problem loading configuration file (%s): %s" % (conf_file, e))

settings.conf['backlog'] = len(settings.conf['connectors'])

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

	handle = io.open("fake.stdin", "r+b")
else:
	#disable echo on terminal 
	enable_echo(sys.stdin, False)

	#allow terminal echo to be enabled back when bridge exits
	atexit.register(enable_echo, sys.stdin.fileno(), True)
	handle = io.open(sys.stdin.fileno(), "rb")

keepcycle = True
#ctrl+c
signal.signal(signal.SIGINT, signal_handler) 
#SIGHUP - 1
signal.signal(signal.SIGHUP, signal_handler) 
#SIGTERM - 15
signal.signal(signal.SIGTERM, signal_handler)


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

for name, connector in shd.items():
	logger.debug("Sending stop signal to %s" % name)
	connector.stop()

logger.debug("Exiting")
sys.exit(0)