import os, sys, logging
import socket, asyncore
import json

from utils import *

class BridgeHandler(asyncore.dispatcher_with_send):
	def __init__(self, sock, name, shm):
		asyncore.dispatcher_with_send.__init__(self, sock)
		self.logger = logging.getLogger("server")
		self.name = name
		self.shm = shm
		self.shm[self.name].register()
		self.checksum = ""
		self.data = ""
		self.logger.debug('BridgeHandler(%s) - started' % self.name)

	#this function must return true only if we have something
	# to write - through socket - to the bridge connector
	def writable(self):
		checksum, entry = self.shm[self.name].stash_get("out")
		if checksum:
			self.checksum = checksum
			self.data = entry
			return True

	def handle_read(self):
		message = self.recv(1024)
		message = message.rstrip()
		self.logger.debug("handle_read (msg) - %s" % message)
		#checksum = hashlib.md5(msg.encode('utf-8')).hexdigest()
		checksum = get_checksum(message, False)
		self.logger.debug("handle_read (checksum) - %s" % checksum)
		if message == "":
			return
		try:
			#TODO this must check if - inside hash - there is the key "data" (raiserror if not)
			entry = json.loads(message)
		except ValueError, e:
			self.logger.debug("String not empty but not JSON: %s" % message)
		else:
			self.shm[self.name].stash_put("in", checksum, entry)
			#we have to return output only if client doesn't specify otherwise
			result = {
				"status" : 1,
				"checksum": checksum
			}
			self.send(json.dumps(result))

	def handle_write(self):
		self.send(json.dumps(self.data))
		self.data = ""
		self.checksum = ""

	def handle_close(self):
		self.logger.debug('BridgeHandler(%s) - ended' % self.name)
		#notify to server that this connector has disconnected
		self.shm[self.name].unregister()

	def handle_error(self):
		nil, t, v, tbinfo = asyncore.compact_traceback()

		# sometimes a user repr method will crash.
		try:
			self_repr = repr(self)
		except:
			self_repr = '<__repr__(self) failed for object at %0x>' % id(self)

		self.logger.debug('BridgeHandler(%s) - uncaptured python exception %s (%s:%s %s)' % (
			self.name, self_repr, t, v, tbinfo
		))
		self.logger.debug('BridgeHandler(%s) - closing channel' % self.name)
		self.close()
		#self.close should trigger handle_close but it seems it doesn't (than we call it manually)
		self.handle_close()


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
						self.clients.append(handler)
			except ValueError, e:
				self.logger.debug('Exception: new client not presented properly %s' % hello)
				sock.close()

	def broadcast_message(self, source_client, message):
		for c in self.clients:
			if c != source_client:
				c.send(message)

def init(conf, shm):
	logging.basicConfig(filename=conf['logfile'],level=logging.DEBUG)
	server = BridgeServer("server", conf, shm)
	asyncore.loop(0.05)