##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import logging
import socket, asyncore
import json

from threading import Thread
from Queue import Queue

#class BridgeHandler(asyncore.dispatcher_with_send):

class BridgeClient(asyncore.dispatcher_with_send):

	host = "127.0.0.1"
	port = 8900
	write_pending = False
	data_pending = None

	def __init__(self, shd, xmpp_queue, socket_queue):
		asyncore.dispatcher_with_send.__init__(self)
		self.shd = shd
		self.xmpp_queue = xmpp_queue
		self.socket_queue = socket_queue

		# load bridge (host, port) configuration if present
		# otherwise it will use default
		if "bridge" in self.shd['conf']:
			if "host" in self.shd['conf']['bridge']:
				self.host = self.shd['conf']['bridge']['host']
			if "port" in self.shd['conf']['bridge']:
				self.port = self.shd['conf']['bridge']['port']
		self.logger = logging.getLogger("xmpp")

	# register function (useful when connector start or reconnect)
	def register(self):
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		params = { "action" : "register", "name" : "xmpp" }
		self.connect((self.host, self.port))
		self.socket.send(json.dumps(params))

	# overriding native asyncore function to handle message received via socket
	def handle_read(self):
		self.logger.debug("Handle READ")
		data = self.recv(2048)
		self.logger.debug("read message: %s" % data)
		if data:
			data_decoded = json.loads(data)
			if "status" in data_decoded:
				if self.write_pending:
					self.shd["requests"][data_decoded["checksum"]] = self.data_pending
					self.data_pending = None
					self.write_pending = False
				else:
					self.logger.warning("result msg but not write_pending: %s" % data)
			else:
				self.xmpp_queue.put(data_decoded)

	# writable/handle_write are function useful ONLY 
	# if the connector offers communication from OUTSIDE WORLD to MCU
	def writable(self):
		if not self.shd["loop"]:
			raise asyncore.ExitNow('Connector is quitting!')
		if not self.socket_queue.empty() and not self.write_pending:
			return True
		return False

	def handle_write(self):
		self.logger.debug("Handle WRITE")
		entry = self.socket_queue.get()

		# we wait a feedback (status + checksum) from bridge
		self.write_pending = True
		self.data_pending = entry
		self.send(json.dumps(entry))

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

		self.logger.error('BridgeClient - python exception %s (%s:%s %s)' % (
			self_repr, t, v, tbinfo
		))
		self.logger.debug("Handle ERROR")
		return

	def exit(self):
		raise asyncore.ExitNow('Connector is quitting!')

class BridgeThread(Thread):
	def __init__(self, shd, xmpp_queue, socket_queue):
		Thread.__init__(self)
		self.daemon = True
		self.shd = shd
		self.client = BridgeClient(shd, xmpp_queue, socket_queue)
		self.client.register()

	def run(self):
		try:
			asyncore.loop(0.05)
		except asyncore.ExitNow, e:
			logger = logging.getLogger("xmpp")
			logger.error("Exception asyncore.ExitNow, closing BridgeSocket. (%s)" % e)

	def stop(self):
		#self.socket.exit()
		#self.socket.close()
		self.join()