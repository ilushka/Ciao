import os, sys, logging
import json, hashlib

import settings
from utils import *

class BridgeConnector(object):
	def __init__(self, name, conf, registered = False):
		self.name = name
		self.registered = registered
		self.logger = logging.getLogger("server")
		self.init_conf(conf)

		#interactions stash
		self.stash = {}

		#list of requests handled with two fifo queues
		# in - OUTSIDE-IN (connectors -> MCU)
		# out - INSIDE-OUT (MCU -> connectors)
		self.fifo = { "in": [], "out": [] }

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

	def stash_get(self, destination):
		#TODO
		# probably we should remove elements from stash (other than from fifo)
		# if destination out and type response we should remove the original read too?
		if len(self.fifo[destination]) > 0:
			checksum = self.fifo[destination].pop(0)
			return checksum, self.stash[checksum]
		return False, False

	# stash store hash elements
	# type: out|result|response
	def stash_put(self, destination, checksum, element):
		self.stash[checksum] = element
		self.fifo[destination].append(checksum)
		return

	def has_result(self, checksum):
		return checksum in self.stash and "result" in self.stash[checksum]

	def get_result(self, checksum):
		return self.stash[checksum]["result"]

	def run(self, short_action, command):
		#retrieve real action value from short one (e.g. "r" => "read" )
		action = settings.allowed_actions[short_action]['map']
		required_params = settings.allowed_actions[short_action]['params']
		if self.is_registered() and action in self.implements:
			params = command.split(";", required_params)
			#TODO
			# required_params must be customizable according with connector
			# after split we need to check if len(params) match expected required_params value
			if self.implements[action] == 'in':
				pos, entry = self.stash_get("in")
				if pos:
					out(1, pos, entry["data"])
				else:
					out(0, "no_message")
			elif self.implements[action] == 'out':
				message = params[required_params - 1]
				checksum = get_checksum(message, False)
				#checksum = hashlib.md5(message.encode('utf-8')).hexdigest()
				data = unserialize(message, False)
				if action == "writeresponse":
					result = {
						"type": "response",
						#checksum of read interaction we are responding to
						"source_checksum": params[2],
						"data": data
					}
				else:
					result = {
						"type": "out",
						"data": data
					}
				self.stash_put("out", checksum, result)
				out(1, "done")
			elif self.implements[action] == 'result':
				message = params[required_params - 1]
				checksum = get_checksum(message)
				#checksum = hashlib.md5(message.encode('utf-8')).hexdigest()
				if not checksum in self.stash:
					result = { 
						"type": "result",
						"data": unserialize(message, False)
					}
					self.stash_put("out", checksum, result)
				elif self.has_result(checksum):
					out(1, checksum, self.get_result(checksum))
				else:
					out(0, "no_result")
			else:
				self.logger.debug("unknown behaviour action: %s" % action)
		else:
			self.logger.debug("asdasdasd")