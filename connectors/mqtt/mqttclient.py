#!/usr/bin/python

import paho.mqtt.client as mqtt

class MQTTClient():

	subscribed_topic = []

	def __init__(self, mqtt_params, ciao_queue):
		#validate params - START (we need to make it before super.__init__)
		missing_params = []
		required_params = ["host", "port"]
		for p in required_params:
			if not p in mqtt_params:
				missing_params.append(p)

		if len(missing_params) > 0:
			raise RuntimeError("MQTT configuration error, missing: %s" % ",".join(missing_params))

		if not mqtt_params["client_id"]:
			mqtt_params['client_id'] = "mqttconnector-pub"

		if not mqtt_params["clean_session"]:
			mqtt_params['clean_session'] = True
		#validate params - END

		#NB you can't use self before __init__ on parent class
		#mqtt.Client.__init__(self, mqtt_params['client_id'])
		self.handle = mqtt.Client(mqtt_params["client_id"], mqtt_params["clean_session"])
		self.handle.on_connect = self.on_connect
		self.handle.on_message = self.on_message

		if mqtt_params["subscribed_topic"]:
			self.subscribed_topic = mqtt_params["subscribed_topic"]

		self.client_id = mqtt_params["client_id"]
		self.host = mqtt_params["host"]
		self.port = mqtt_params["port"]

		#TODO we need to add will_set (to establish something to do on LastWill and Testament, for unwanted disconnection)
		#TODO implements authentication params
		self.ciao_queue = ciao_queue

	def on_connect(self, client, userdata, flags, rc):
		print "Connected with result code "+str(rc)
		#TODO log connection status

	def on_message(self, client, userdata, msg):
		#print msg.topic + " " + str(msg.payload)
		#TODO log msg content
		entry = {
			"data" : [str(msg.topic), str(msg.payload)]
		}
		self.ciao_queue.put(entry)

	def connect(self):
		if self.handle.connect(self.host, self.port, 60) == 0:
			for topic in self.subscribed_topic:
				self.handle.subscribe(str(topic), qos=0)
			self.handle.loop_start()
			return True
		return False

	def disconnect(self):
		self.handle.loop_stop()
		self.handle.disconnect()

	def publish(self, topic, message, qos=2):
		self.handle.publish(topic, message, qos)