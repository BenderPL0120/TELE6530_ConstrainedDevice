#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# You may find it more helpful to your design to adjust the
# functionality, constants and interfaces (if there are any)
# provided within in order to meet the needs of your specific
# Programming the Internet of Things project.
# 

import logging
import uuid
import paho.mqtt.client as mqttClient

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

class MqttClientConnector(IPubSubClient):
	"""
	Shell representation of class for student implementation.
	
	"""

	def __init__(self, clientID: str = None):
		"""
		Default constructor. This will set remote broker information and client connection
		information based on the default configuration file contents.
		
		@param clientID Defaults to None. Can be set by caller. If this is used, it's
		critically important that a unique, non-conflicting name be used so to avoid
		causing the MQTT broker to disconnect any client using the same name. With
		auto-reconnect enabled, this can cause a race condition where each client with
		the same clientID continuously attempts to re-connect, causing the broker to
		disconnect the previous instance.
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = None
		
		# Read MQTT configuration from config file
		self.host = self.config.getProperty(
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		
		self.port = self.config.getInteger(
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_MQTT_PORT)
		
		self.keepAlive = self.config.getInteger(
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.KEEP_ALIVE_KEY, ConfigConst.DEFAULT_KEEP_ALIVE)
		
		self.defaultQos = self.config.getInteger(
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.DEFAULT_QOS_KEY, ConfigConst.DEFAULT_QOS)
		
		self.mqttClient = None
		
		# Set client ID - use provided one or get from config
		if not clientID:
			self.clientID = self.config.getProperty(
					ConfigConst.CONSTRAINED_DEVICE, ConfigConst.DEVICE_LOCATION_ID_KEY)
		else:
			self.clientID = clientID
		
		# Validate clientID exists
		if not self.clientID:
			self.clientID = "CDA-" + str(uuid.uuid4())  # Generate random ID if needed
		
		# Log configuration info
		logging.info('\tMQTT Client ID:   ' + self.clientID)
		logging.info('\tMQTT Broker Host: ' + self.host)
		logging.info('\tMQTT Broker Port: ' + str(self.port))
		logging.info('\tMQTT Keep Alive:  ' + str(self.keepAlive))
		
	def connectClient(self) -> bool:
		if not self.mqttClient:
			# Create MQTT client instance with callbacks
			self.mqttClient = mqttClient.Client(client_id=self.clientID, clean_session=True)
			
			# Set callback handlers
			self.mqttClient.on_connect = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message = self.onMessage
			self.mqttClient.on_publish = self.onPublish
			self.mqttClient.on_subscribe = self.onSubscribe
		
		if not self.mqttClient.is_connected():
			logging.info('MQTT client connecting to broker at host: ' + self.host)
			self.mqttClient.connect(self.host, self.port, self.keepAlive)
			self.mqttClient.loop_start()  # Start network loop in background thread
			return True
		else:
			logging.warning('MQTT client is already connected. Ignoring connect request.')
			return False
		
	def disconnectClient(self) -> bool:
		if self.mqttClient and self.mqttClient.is_connected():
			logging.info('Disconnecting MQTT client from broker: ' + self.host)
			self.mqttClient.loop_stop()  # Stop the network loop
			self.mqttClient.disconnect()
			return True
		else:
			logging.warning('MQTT client already disconnected. Ignoring.')
			return False
		
	def onConnect(self, client, userdata, flags, rc):
		if rc == 0:
			logging.info('MQTT client connected to broker: ' + str(client))
		else:
			logging.error('Failed to connect with result code: ' + str(rc))
		
	def onDisconnect(self, client, userdata, rc):
		if rc == 0:
			logging.info('MQTT client disconnected from broker: ' + str(client))
		else:
			logging.warning('MQTT client unexpectedly disconnected with code: ' + str(rc))
		
	def onMessage(self, client, userdata, msg):
		payload = msg.payload
		
		if payload:
			# decode the byte array to a UTF-8 string
			payloadStr = payload.decode("utf-8")
			logging.info('MQTT message received on topic [' + msg.topic + '] with payload: ' + payloadStr)
		else:
			logging.info('MQTT message received with no payload: ' + str(msg))
			
	def onPublish(self, client, userdata, mid):
		logging.info('MQTT message published: ' + str(client))
	
	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info('MQTT client subscribed: ' + str(client))
	
	def onActuatorCommandMessage(self, client, userdata, msg):
		"""
		This callback is defined as a convenience, but does not
		need to be used and can be ignored.
		
		It's simply an example for how you can create your own
		custom callback for incoming messages from a specific
		topic subscription (such as for actuator commands).
		
		@param client The client reference context.
		@param userdata The user reference context.
		@param msg The message context, including the embedded payload.
		"""
		pass
	
	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS):
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot publish message.')
			return False
		
		# check validity of message
		if not msg:
			logging.warning('No message specified. Cannot publish message to topic: ' + resource.value)
			return False
		
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			logging.warning('Invalid QoS level %d. Using default: %d', qos, ConfigConst.DEFAULT_QOS)
			qos = ConfigConst.DEFAULT_QOS
	 
		# check the client is connected
		if not self.mqttClient or not self.mqttClient.is_connected():
				logging.error('MQTT client not connected. Cannot publish message.')
				return False
	
		try:
			# publish the message
			msgInfo = self.mqttClient.publish(topic=resource.value, payload=msg, qos=qos)
			
			# wait for publish to complete
			msgInfo.wait_for_publish()
			
			if msgInfo.is_published():
				logging.debug('Successfully published message to topic: ' + resource.value)
				return True
			else:
				logging.error('Failed to publish message to topic: ' + resource.value)
				return False
		except Exception as e:
			logging.error('Exception while publishing message: ' + str(e))
			return False

	def subscribeToTopic(self, resource: ResourceNameEnum = None, callback=None, qos: int = ConfigConst.DEFAULT_QOS):
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot subscribe.')
			return False
		
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
	 
	 	# check the client is connected
		if not self.mqttClient or not self.mqttClient.is_connected():
			logging.error('MQTT client not connected. Cannot subscribe to topic.')
			return False
		
		try:
			# subscribe to topic
			logging.info('Subscribing to topic: %s with QoS: %d', resource.value, qos)
			result, mid = self.mqttClient.subscribe(resource.value, qos)
			
			# check result
			if result == mqttClient.MQTT_ERR_SUCCESS:
				logging.info('Successfully subscribed to topic: %s (message ID: %d)', resource.value, mid)
				return True
			else:
				logging.error('Failed to subscribe to topic: %s (error code: %d)', resource.value, result)
				return False
		except Exception as e:
			logging.error('Exception while subscribing to topic: ' + str(e))
			return False

	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None):
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot unsubscribe.')
			return False
 
		# check the client is connected
		if not self.mqttClient or not self.mqttClient.is_connected():
			logging.error('MQTT client not connected. Cannot unsubscribe from topic.')
			return False
		
		try:
			# unsubscribe from topic
			logging.info('Unsubscribing from topic: %s', resource.value)
			result, mid = self.mqttClient.unsubscribe(resource.value)

			# check result
			if result == mqttClient.MQTT_ERR_SUCCESS:
				logging.info('Successfully unsubscribed from topic: %s (message ID: %d)', resource.value, mid)
				return True
			else:
				logging.error('Failed to unsubscribe from topic: %s (error code: %d)', resource.value, result)
				return False
		except Exception as e:
			logging.error('Exception while unsubscribing from topic: ' + str(e))
			return False

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		return False
