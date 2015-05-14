from Queue import Queue
import socket
import termios
import logging

#SETTINGS
allowed_actions = {
	"r": { "params": 3, "map": "read"},				#requires 2 params - connector;action
	"w": { "params": 3, "map": "write"},			#requires 3 params - connector;action;data
	"wr": { "params": 4, "map": "writeresponse"}	#requires 4 params - connector;action;reference;data
}

#METHODS

#enable/disable echo on tty
def enable_echo(fd, enabled):
	(iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(fd)
	if enabled:
		lflag |= termios.ECHO
	else:
		lflag &= ~termios.ECHO
	new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
	termios.tcsetattr(fd, termios.TCSANOW, new_attr)

def clean_command(command):
	return command.rstrip()

def is_valid_command(command):
	global allowed_actions
	#a valid command must contain at least two fields: connector and action
	elements = command.split(";", 2)
	if len(elements) >= 2 and elements[1] in allowed_actions:
		return elements
	return False, False

#CLASSES
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
		global allowed_actions
		#retrieve real action value from short one (i.e. "r" => "read" )
		action = allowed_actions[short_action]['map']
		if action in self.implements:
			params = command.split()
			self.logger.debug("implements %s " % self.implements)
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