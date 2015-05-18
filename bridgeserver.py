import asyncore
import socket
import os
import sys
import logging
#from bridgeutils import BridgeConnector
import json

class BridgeHandler(asyncore.dispatcher_with_send):
	def __init__(self, sock, name, shm):
		asyncore.dispatcher_with_send.__init__(self, sock)
		self.logger = logging.getLogger("server")
		self.name = name
		self.shm = shm
		self.shm[self.name].register()
		self.data = ""
		self.logger.debug('BridgeHandler(%s) - started' % name)

	#this function must return true only if we have something
	# to write - through socket - to the bridge connector
	def writable(self):
		entry = self.shm[self.name].queue_pull()
		if entry:
			self.data = entry
			return True

	def handle_read(self):
		msg = self.recv(1024)
		msg = msg.rstrip()
		if msg == "":
			return
		try:
			json.loads(msg)
		except ValueError, e:
			self.logger.debug("string not empty but wrong: %s" % msg)
		else:
			position = self.shm[self.name].put_message(msg)
			#we have to return output only if client doesn't specify otherwise
			data = {
				"status" : 200,
				"queue_id": position
			}
			self.send(json.dumps(data))

	def handle_write(self):
		self.send(self.data)
		self.data = ""

	def handle_close(self):
		self.logger.debug('bridgehandler - ended')
		self.close()
		#notify to server that this connector has disconnected
		self.shm[self.name].unregister()

	def handle_error(self, type = None, value = None, traceback = None):
		#self.logger.debug('bridgehandler - ended(due to error) %s %s %s ' % type, value, traceback)
		self.close()
		#notify to server that this connector has disconnected
		self.shm[self.name].unregister()

class BridgeServer(asyncore.dispatcher):
	def __init__(self, name, conf, shm):
		asyncore.dispatcher.__init__(self)
		self.srv_name = name
		self.clients = []
		self.shm = shm

		#creating server socket
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((conf['srvhost'], conf['srvport']))
		self.listen(conf['backlog'])

		self.logger = logging.getLogger("server")

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			self.logger.debug('Incoming connection from %s', repr(addr))

			#new client has to present itself (action:register)
			hello = sock.recv(1024)
			try:
				data = json.loads(hello)		
				if not data['action'] or data['action'] != 'register' or not data['name']:
					self.logger.debug('New client not presented properly %s' % hello)
					sock.close()
				else:
					self.logger.debug('Registering new connector with name %s' % data['name'])
					if not data['name'] in self.shm:
						self.logger.debug('No connectors enabled with name %s' % data['name'])
						sock.close()
					else:
						handler = BridgeHandler(sock, data['name'], self.shm)
						#self.shm[data['name']].register(handler)
						self.clients.append(handler)
						#handler.send("welcome on %s\r\n" % self.srv_name)
			except ValueError, e:
				self.logger.debug('Exception: new client not presented properly %s' % hello)
				sock.close()
			#self.broadcast_message(handler, "%s:%s just entered\r\n" % addr)

	def broadcast_message(self, new_client, message):
		for c in self.clients:
			if c != new_client:
				c.send(message)

def init(conf, shm):
	logging.basicConfig(filename=conf['logfile'],level=logging.DEBUG)
	server = BridgeServer("server", conf, shm)
	asyncore.loop(0.05)