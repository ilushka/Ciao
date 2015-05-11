#from multiprocessing import Queue
from Queue import Queue
import socket
"""
try:
    import cPickle as pickle
except:
    import pickle
"""

class BridgeConnector(object):
	def __init__(self, name, queue, registered = False):
		self.name = name
		self.queue = queue
		self.registered = registered
		#requests stash
		self.stash = []
		#list of request to be read
		self.fifo = []

	def is_registered(self):
		return self.registered

	def queue_push(self, entry):
		self.queue.put(entry)

	def queue_pull(self):
		if not self.queue.empty():
			return self.queue.get_nowait()
		return

	def has_message(self):
		return len(self.fifo) > 0

	def get_message(self):
		if len(self.fifo) > 0:
			position = self.fifo.pop()
			return position, self.stash[position]
		return False

	def put_message(self, message):
		self.stash.append(message)
		position = len(self.stash) - 1
		self.fifo.append(position)
		return position

	def register(self):
		#if already registered we should return false (avoiding duplication)
		self.registered = True

	def unregister(self):
		self.registered = False
"""
	def __reduce__(self):
		return (self.__class__,(self.name, self.queue, self.is_registered))
"""
