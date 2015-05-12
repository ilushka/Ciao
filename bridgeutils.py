from Queue import Queue
import socket

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
			position = self.fifo.pop(0)
			return ";".join(map(str,[position, self.stash[position]]))
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

#utils methods
def clean_command(command):
	return command.rstrip()

def get_params(command, logger):
	logger.debug("get_params: %s" % command)
	#explode command string in up to three pieces
	return command.split(";", 2)

def is_valid_command(params, logger):
	allowed_actions = {"w":3, "r":2, "wr":3}
	if len(params) > 1:
		if params[1] in allowed_actions and len(params) >= allowed_actions[params[1]]:
			return True
	return False