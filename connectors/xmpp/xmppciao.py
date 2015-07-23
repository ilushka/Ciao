#!/usr/bin/python
##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import logging
import socket, asyncore
import json

from ciaotools import CiaoThread

class XMPPCiao(CiaoThread):
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
				self.connector_queue.put(data_decoded)

	# writable/handle_write are function useful ONLY 
	# if the connector offers communication from OUTSIDE WORLD to MCU
	def writable(self):
		if not self.shd["loop"]:
			raise asyncore.ExitNow('Connector is quitting!')
		if not self.ciao_queue.empty() and not self.write_pending:
			return True
		return False

	def handle_write(self):
		self.logger.debug("Handle WRITE")
		entry = self.ciao_queue.get()

		# we wait a feedback (status + checksum) from ciao
		self.write_pending = True
		self.data_pending = entry
		self.send(json.dumps(entry))