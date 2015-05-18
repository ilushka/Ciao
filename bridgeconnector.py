import logging
import settings
import json
import sys
import os
from Queue import Queue
from utils import *

class BridgeConnector(object):
	def __init__(self, name, conf, queue, registered = False):
		self.name = name
		self.queue = queue
		self.registered = registered
		self.logger = logging.getLogger("server")
		self.init_conf(conf)

		#requests stash
		self.stash = []
		#list of request to be read
		self.fifo = []

	def init_conf(self, conf):
		if "implements" in conf:
			self.implements = conf['implements']

	def is_registered(self):
		return self.registered

	def register(self):
		#if already registered we should return false (avoiding duplication)
		self.registered = True

	def unregister(self):
		self.registered = False

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
			position = self.fifo.pop(0)
			return position, self.stash[position]
		return False

	def put_message(self, message):
		self.stash.append(message)
		position = len(self.stash) - 1
		self.fifo.append(position)
		return position

	def run(self, short_action, command):
		#retrieve real action value from short one (i.e. "r" => "read" )
		action = settings.allowed_actions[short_action]['map']
		if action in self.implements and self.is_registered():
			params = command.split(";")
			#this must be properly fixed
			if self.implements[action] == 'with_queue':
				data = array.array("B")
				if len(params) > 2:
					for c in params[2]:
						data.append(ord(c))
				data = json.dumps(unserialize(data))
				self.queue_push(data)
				print "1;done"
			elif self.implements[action] == 'with_message':
				if self.has_message():
					pos, msg = self.get_message()
					msg = json.loads(msg)
					os.write(sys.stdout.fileno(), "1;"+str(pos)+";")
					output = serialize(msg)
					os.write(sys.stdout.fileno(), output.tostring())
				else:
					print "0;no_message"
			else:
				self.logger.debug("underground")
		else:
			self.logger.debug("asdasdasd")