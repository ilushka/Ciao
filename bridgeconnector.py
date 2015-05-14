import logging
import settings
from Queue import Queue

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
			return ";".join(map(str,[position, self.stash[position]]))
		return False

	def put_message(self, message):
		self.stash.append(message)
		position = len(self.stash) - 1
		self.fifo.append(position)
		return position

	def run(self, short_action, command):
		#retrieve real action value from short one (i.e. "r" => "read" )
		action = settings.allowed_actions[short_action]['map']
		if action in self.implements:
			params = command.split()
			if self.implements[action] == 'with_queue':
				self.queue_push(params[2])
				print "1;done"
			elif self.implements[action] == 'with_message':
				if self.has_message():
					print "1;"+self.get_message()
				else:
					print "0;no_message"
			else:
				self.logger.debug("underground")
		else:
			self.logger.debug("asdasdasd")