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

import json
import sleekxmpp

# extending sleekxmpp.ClientXMPP to implement some custom features
class XMPPClient(sleekxmpp.ClientXMPP):

	data_rx = [None]

	def __init__(self, xmpp_params, socket_queue):
		#validate params - START (we need to make it before super.__init__)
		missing_params = []
		required_params = ["host", "port", "username", "password"]
		for p in required_params:
			if not p in xmpp_params:
				missing_params.append(p)

		if len(missing_params) > 0:
			raise RuntimeError("XMPP configuration error, missing: %s" % ",".join(missing_params))

		#setting up user/password
		jabberid = xmpp_params["username"]
		password = xmpp_params["password"]

		if "domain" in xmpp_params:
			jabberid += "@" + xmpp_params["domain"]
		else:
			jabberid += "@" + xmpp_params["host"]

		#validate params - END

		sleekxmpp.ClientXMPP.__init__(self, jabberid, password)
	
		self.socket_queue = socket_queue
		self.jabberid = jabberid
		self.password = password
		self.host = xmpp_params["host"]
		self.port = xmpp_params["port"]
		self.tls = True if not "tls" in xmpp_params else xmpp_params["tls"]
		self.ssl = False if not "ssl" in xmpp_params else xmpp_params["ssl"]

		self.auto_reconnect = True

		# The session_start event will be triggered when
		# the bot establishes its connection with the server
		# and the XML streams are ready for use. We want to
		# listen for this event so that we we can initialize
		# our roster.
		self.add_event_handler("session_start", self.start)
		
		# The message event is triggered whenever a message
		# stanza is received. Be aware that that includes
		# MUC messages and error messages.
		self.add_event_handler("message", self.message)

		# Service Discovery
		self.register_plugin('xep_0030')
		# Data Forms
		self.register_plugin('xep_0004')
		# PubSub
		self.register_plugin('xep_0060')
		# XMPP Ping
		self.register_plugin('xep_0199')

	def connect(self):
		result = super(sleekxmpp.ClientXMPP, self).connect(self.host, self.port, use_tls = self.tls, use_ssl = self.ssl)
		if result:
			self.process(block=False)
		return result

	def start(self, event):
		self.send_presence()
		self.get_roster()

	def message(self, msg):
		"""
		Process incoming message stanzas. Be aware that this also
		includes MUC messages and error messages. It is usually
		a good idea to check the messages's type before processing
		or sending replies.

		Arguments:
			msg -- The received message stanza. See the documentation
				   for stanza objects and the Message stanza to see
				   how it may be used.
		"""
		
		if msg['type'] in ('chat', 'normal'):
			entry = {
				"data" : [str(msg["from"]), str(msg["body"])]
			}
			self.socket_queue.put(entry)
