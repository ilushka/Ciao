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
#
###

from Queue import Queue
import time, logging
import paho.mqtt.client as mqtt

class MQTTClient():

	subscribed_topic = []

	def __init__(self, mqtt_params, ciao_queue):
		#validate params - START
		missing_params = []
		required_params = ["host", "port", "client_id"]
		for p in required_params:
			if not p in mqtt_params:
				missing_params.append(p)

		if len(missing_params) > 0:
			raise RuntimeError("MQTT configuration error, missing: %s" % ",".join(missing_params))

		if not mqtt_params["clean_session"]:
			mqtt_params['clean_session'] = True

		if not "qos" in mqtt_params:
			mqtt_params["qos"] = 2

		#validate params - END

		#saving local reference to logger
		self.logger = logging.getLogger("mqtt.client")

		#reference to Queue for exchanging data with CiaoCore
		self.ciao_queue = ciao_queue

		#local instance of MQTT Client
		while True:
			try:
				self.handle = mqtt.Client(mqtt_params["client_id"], mqtt_params["clean_session"])
			except Exception, e:
				self.logger.error("Problem with mqtt.Client: %s" % e)
				time.sleep(1)
			else:
				self.logger.debug("MQTT.Client created")
				break
		self.handle.on_connect = self.on_connect
		self.handle.on_message = self.on_message

		if mqtt_params["subscribed_topic"]:
			self.subscribed_topic = mqtt_params["subscribed_topic"]

		self.client_id = mqtt_params["client_id"]
		self.host = mqtt_params["host"]
		self.port = mqtt_params["port"]
		self.qos = mqtt_params["qos"]

		#SET authentication params (retrieved from configuration file under mqtt/mqtt.json.conf)
		self.logger.debug("Setting username/password...")
		if mqtt_params["username"] and mqtt_params["password"]:
			self.handle.username_pw_set(str(mqtt_params["username"]), str(mqtt_params["password"]))

		#SET LWT (Last Will & Testament) params for unwanted disconnection
		if mqtt_params["lwt_topic"] and mqtt_params["lwt_message"]:
			self.logger.debug("Setting LWT...")
			self.handle.will_set(str(mqtt_params["lwt_topic"]), str(mqtt_params["lwt_message"]), qos=self.qos)

	def on_connect(self, client, userdata, flags, rc):
		self.logger.info ("Connected to MQTT broker with result code %s" % str(rc))
		for topic in self.subscribed_topic:
			if topic: #prevent issues from specifying empty topic
				self.handle.subscribe(str(topic), qos=self.qos)

	def on_message(self, client, userdata, msg):
		self.logger.debug("Got new message. Topic: %s Message: %s" % (str(msg.topic), str(msg.payload)))
		entry = {
			"data" : [str(msg.topic), str(msg.payload)]
		}
		self.ciao_queue.put(entry)

	def connect(self):
		self.logger.debug("Connecting to server...")
		connected = False
		while not connected:
			try:
				if self.handle.connect(self.host, self.port, 60) == 0:
					connected = True
			except Exception, e:
				self.logger.error("Problem creating %s socket: %s" % (__name__, e))
				time.sleep(2)
		if connected:
			self.handle.loop_start()
		return connected

	def disconnect(self):
		self.handle.loop_stop()
		self.handle.disconnect()

	def publish(self, topic, message, qos=None):
		if not qos:
			qos = self.qos
		self.logger.debug("Publishing message. Topic: %s Message: %s" % (topic, str(message)))
		self.handle.publish(topic, str(message), qos)
