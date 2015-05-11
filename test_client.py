import asyncore
import json
import socket

class TestClient(asyncore.dispatcher_with_send):
	def __init__(self, host):
		asyncore.dispatcher_with_send.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect( (host, 8900) )
		self.data =  json.dumps({ "action": "register", "name" : "xmpp"})

	def writable(self):
		return len(self.data) > 0

	def handle_close(self):
		self.close()

	def handle_read(self):
		msg = self.recv(1024)
		print msg

	def handle_write(self):
		self.send(self.data)
		self.data = ""

test = TestClient("localhost")
asyncore.loop(1)