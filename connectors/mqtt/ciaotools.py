##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import logging
import socket, asyncore
import json

from threading import Thread
from Queue import Queue

class CiaoThread(Thread, asyncore.dispatcher_with_send):

	# "name" must be specified in __init__ method
	name = "ciaothread"

	host = "127.0.0.1"
	port = 8900
	write_pending = False
	data_pending = None

	def __init__(self, shd, connector_queue, ciao_queue):
		Thread.__init__(self)
		self.daemon = True

		asyncore.dispatcher_with_send.__init__(self)
		self.shd = shd
		
		self.ciao_queue = ciao_queue
		self.connector_queue = connector_queue

		if "name" in self.shd['conf']:
			self.name = self.shd['conf']['name']

		# load Ciao (host, port) configuration if present
		# otherwise it will use default
		if "ciao" in self.shd['conf']:
			if "host" in self.shd['conf']['ciao']:
				self.host = self.shd['conf']['ciao']['host']
			if "port" in self.shd['conf']['ciao']:
				self.port = self.shd['conf']['ciao']['port']
		self.logger = logging.getLogger(self.name)

		while not self.register():
			# IDEAS: here we could add a max_retry param
			time.sleep(10)

	def run(self):
		try:
			asyncore.loop(0.05)
		except asyncore.ExitNow, e:
			self.logger.error("Exception asyncore.ExitNow, closing CiaoThread. (%s)" % e)

	def stop(self):
		#self.socket.exit()
		#self.socket.close()
		self.join()

	def exit(self):
		raise asyncore.ExitNow('Connector is quitting!')

	# register function (useful when connector start or reconnect)
	def register(self):
		try:
			self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
			params = { "action" : "register", "name" : self.name }
			self.connect((self.host, self.port))
			self.socket.send(json.dumps(params))
		except Exception, e:
			self.logger.error("Problem connecting to server: %s" % e)
			return False
		else:
			return True

	# function to handle socket close
	def handle_close(self):
		self.logger.debug("Handle CLOSE")
		self.close()
		return

	# function to handle error over socket (and close it if necessary)
	def handle_error(self):
		nil, t, v, tbinfo = asyncore.compact_traceback()

		# sometimes a user repr method will crash.
		try:
			self_repr = repr(self)
		except:
			self_repr = '<__repr__(self) failed for object at %0x>' % id(self)

		self.logger.error('CiaoThread - python exception %s (%s:%s %s)' % (
			self_repr, t, v, tbinfo
		))
		self.logger.debug("Handle ERROR")
		return
