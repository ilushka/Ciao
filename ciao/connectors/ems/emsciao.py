###
# This file is part of Arduino Ciao
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# Copyright 2015 Arduino Srl (http://www.arduino.org/)
# 
# authors:
# _giuseppe[at]arduino[dot]org
# _fabriziodevita92[at]gmail[dot]com
#
###

import logging
import socket, asyncore
import json

from ciaotools import CiaoThread

class EMSCiao(CiaoThread):

	def handle_read(self):
		""" handle read from socket because MCU wrote something (asyncore func) """

		self.logger.debug("Handle READ")
		data = self.recv(2048)
		self.logger.debug("read message: %s" % data)

		# calling decode_multiple (from ciaoThread) to handle multiple string at once from Core
		for data_decoded in self.decode_multiple(data):
			if "status" in data_decoded:
				if self.write_pending:
					self.shd["requests"][data_decoded["checksum"]] = self.data_pending
					self.data_pending = None
					self.write_pending = False
				else:
					self.logger.warning("result msg but not write_pending: %s" % data)
			else:
				self.connector_queue.put(data_decoded)

	def writable(self):
		""" is there data to write to MCU (asyncore func) """
		if not self.shd["loop"]:
			raise asyncore.ExitNow('Connector is quitting!')
		if not self.ciao_queue.empty() and not self.write_pending:
			return True
		return False

	def handle_write(self):
		""" handle write to socket to send something to MCU that's ready to receive (asyncore func) """

		self.logger.debug("Handle WRITE")
		entry = self.ciao_queue.get()
		self.logger.debug("MONKEY: " + json.dumps(entry))

		# we wait a feedback (status + checksum) from ciao
		self.write_pending = True
		self.data_pending = entry
		self.send(json.dumps(entry))

