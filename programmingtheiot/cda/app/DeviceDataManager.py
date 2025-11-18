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
import concurrent.futures

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.data.DataUtil import DataUtil

from programmingtheiot.cda.connection.CoapServerAdapter import CoapServerAdapter
from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector

from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager

from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class DeviceDataManager(IDataMessageListener):
	"""
	Shell representation of class for student implementation.
	
	"""
	
	def __init__(self):
		self.configUtil = ConfigUtil()
		self.dataUtil = DataUtil()
		
		# Load configuration settings
		self.enableSystemPerf = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, 
			key=ConfigConst.ENABLE_SYSTEM_PERF_KEY
		)
		self.enableSensing = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, 
			key=ConfigConst.ENABLE_SENSING_KEY
		)
		try:
			self.enableActuation = self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, 
				key=ConfigConst.ENABLE_ACTUATION_KEY
			)
		except:
			self.enableActuation = True
		
		# Initialize managers
		self.sysPerfMgr = None
		self.sensorAdapterMgr = None
		self.actuatorAdapterMgr = None
		
		# Initialize connection clients (for Part III)
		self.mqttClient = None
		self.coapClient = None
		self.coapServer = None

		# Initialize MQTT client 
		self.enableMqttClient = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, 
			key=ConfigConst.ENABLE_MQTT_CLIENT_KEY
		)

		if self.enableMqttClient:
			self.mqttClient = MqttClientConnector()
			self.mqttClient.setDataMessageListener(self)
			logging.info("MQTT client connector initialized")

		# Initialize CoAP server
		self.enableCoapServer = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, 
			key=ConfigConst.ENABLE_COAP_SERVER_KEY
		)
		
		if self.enableCoapServer:
			self.coapServer = CoapServerAdapter(dataMsgListener=self)
			logging.info("CoAP server connector initialized")

  	# Initialize CoAP client
		self.enableCoapClient = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE,
			key=ConfigConst.ENABLE_COAP_CLIENT_KEY
		)
		
		if self.enableCoapClient:
			self.coapClient = CoapClientConnector(dataMsgListener=self)
			logging.info("CoAP client connector initialized")

		# Data caches
		self.sensorDataCache = {}
		self.actuatorResponseCache = {}
		self.sysPerfDataCache = {}
		
		# Setup managers based on configuration
		if self.enableSystemPerf:
			self.sysPerfMgr = SystemPerformanceManager()
			self.sysPerfMgr.setDataMessageListener(self)
			logging.info("Local system performance tracking enabled")
		
		if self.enableSensing:
			self.sensorAdapterMgr = SensorAdapterManager()
			self.sensorAdapterMgr.setDataMessageListener(self)
			logging.info("Local sensor tracking enabled")
		
		if self.enableActuation:
			self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener=self)
			logging.info("Local actuation capabilities enabled")

		# Load Humidity control settings
		self.handleHumidityChangeOnDevice = self.configUtil.getBoolean(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.HANDLE_HUMIDITY_CHANGE_ON_DEVICE_KEY
		)
		self.triggerHumidifierFloor = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_HUMIDIFIER_FLOOR_KEY
		)
		self.triggerHumidifierCeiling = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_HUMIDIFIER_CEILING_KEY
		)

		# Load Temperature control settings
		self.handleTempChangeOnDevice = self.configUtil.getBoolean(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY
		)
		self.triggerHvacTempFloor = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY
		)
		self.triggerHvacTempCeiling = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY
		)

		# Load Pressure control settings
		self.handlePressureChangeOnDevice = self.configUtil.getBoolean(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.HANDLE_PRESSURE_CHANGE_ON_DEVICE_KEY
		)
		self.triggerPressureFloor = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_PRESSURE_FLOOR_KEY
		)
		self.triggerPressureCeiling = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE, 
			ConfigConst.TRIGGER_PRESSURE_CEILING_KEY
		)
  
		# Create a thread pool executor for handling upstream transmissions asynchronously
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
		
	def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
		"""
		Retrieves the named actuator data (response) item from the internal data cache.
		
		@param name
		@return ActuatorData
		"""
		if name and name in self.actuatorResponseCache:
			return self.actuatorResponseCache[name]
		return None
		
	def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
		"""
		Retrieves the named sensor data item from the internal data cache.
		
		@param name
		@return SensorData
		"""
		if name and name in self.sensorDataCache:
			return self.sensorDataCache[name]
		return None
	
	def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
		"""
		Retrieves the named system performance data from the internal data cache.
		
		@param name
		@return SystemPerformanceData
		"""
		if name and name in self.sysPerfDataCache:
			return self.sysPerfDataCache[name]
		return None
	
	def handleActuatorCommandMessage(self, data: ActuatorData) -> ActuatorData:
		"""
		This callback method will be invoked by the connection that's handling
		an incoming ActuatorData command message.
		
		@param data The incoming ActuatorData command message.
		@return ActuatorData
		"""
		if data:
			logging.info(f"Processing actuator command message: {data}")
		
			# TODO: add further validation before sending the command
			return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Received invalid ActuatorData command message. Ignoring.")
			return None
	
	def handleActuatorCommandResponse(self, data: ActuatorData) -> bool:
		"""
		This callback method will be invoked by the actuator manager that just
		processed an ActuatorData command, which creates a new ActuatorData
		instance and sets it as a response before calling this method.
		
		@param data The incoming ActuatorData response message.
		@return boolean
		"""
		if data:
			logging.debug(f"Actuator response received: {data}")
			
			# Cache the response
			self.actuatorResponseCache[data.getName()] = data
			
			# Prepare for upstream transmission
			actuatorMsg = self.dataUtil.actuatorDataToJson(data)
			resourceName = ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE
			
			self._handleUpstreamTransmission(resourceName=resourceName, msg=actuatorMsg)
			return True
		else:
			logging.warning("Invalid actuator response (null). Ignoring.")
			return False
	
	def handleIncomingMessage(self, resourceEnum: ResourceNameEnum, msg: str) -> bool:
		"""
		This callback method is generic and designed to handle any incoming string-based
		message, which will likely be JSON-formatted and need to be converted to the appropriate
		data type. You may not need to use this callback at all.
		
		@param data The incoming JSON message.
		@return boolean
		"""
		logging.info(f"Processing incoming message for resource: {resourceEnum}")
		
		if msg:
			self._handleIncomingDataAnalysis(msg)
			return True
		return False
	
	def handleSensorMessage(self, data: SensorData) -> bool:
		"""
		This callback method will be invoked by the sensor manager that just processed
		a new sensor reading, which creates a new SensorData instance that will be
		passed to this method.
		
		@param data The incoming SensorData message.
		@return boolean
		"""
		if data:
			logging.debug(f"Sensor data received: {data}")
			
			# Cache the sensor data
			self.sensorDataCache[data.getName()] = data
			
			# Perform local analysis
			self._handleSensorDataAnalysis(data)
			
			# Prepare for upstream transmission
			sensorMsg = self.dataUtil.sensorDataToJson(data)
			resourceName = ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE
			
			self._handleUpstreamTransmission(resourceName=resourceName, msg=sensorMsg)
			return True
		else:
			logging.warning("Invalid sensor data (null). Ignoring.")
			return False
	
	def handleSystemPerformanceMessage(self, data: SystemPerformanceData) -> bool:
		"""
		This callback method will be invoked by the system performance manager that just
		processed a new sensor reading, which creates a new SystemPerformanceData instance
		that will be passed to this method.
		
		@param data The incoming SystemPerformanceData message.
		@return boolean
		"""
		if data:
			logging.debug(f"System performance data received: {data}")
			
			# Cache the data
			self.sysPerfDataCache[data.getName()] = data
			
			# Prepare for upstream transmission
			sysPerfMsg = self.dataUtil.systemPerformanceDataToJson(data)
			resourceName = ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE
			
			self._handleUpstreamTransmission(resourceName=resourceName, msg=sysPerfMsg)
			return True
		else:
			logging.warning("Invalid system performance data (null). Ignoring.")
			return False
	
	def setSystemPerformanceDataListener(self, listener: ISystemPerformanceDataListener = None):
		pass
			
	def setTelemetryDataListener(self, name: str = None, listener: ITelemetryDataListener = None):
		pass
			
	def startManager(self):
		"""
		Initialize and start all configured subsystem managers.
		"""
		logging.info("Starting DeviceDataManager...")
		
		try:
			if self.sysPerfMgr:
				self.sysPerfMgr.startManager()
				
			if self.sensorAdapterMgr:
				self.sensorAdapterMgr.startManager()
		
	 		# connect MQTT client if enabled
			if self.mqttClient:
				logging.info("Connecting MQTT client...")
				self.mqttClient.connectClient()

				# # Subscribe to actuator command topic
				# self.mqttClient.subscribeToTopic(
				# 	ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				# 	callback=self.handleActuatorCommandMessage,
				# 	qos=ConfigConst.DEFAULT_QOS
				# )

			# Start CoAP server if enabled
			if self.coapServer:
				logging.info("Starting CoAP server...")
				self.coapServer.startServer()
				logging.info("CoAP server started")
				
			logging.info("DeviceDataManager started successfully")
		except Exception as e:
			logging.error(f"Failed to start DeviceDataManager: {e}")
			raise
		
	def stopManager(self):
		"""
		Gracefully shutdown all subsystem managers.
		"""
		logging.info("Stopping DeviceDataManager...")
		
		try:
	 		# disconnect MQTT client if enabled
			if self.mqttClient:
				logging.info("Disconnecting MQTT client...")
				self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
				self.mqttClient.disconnectClient()
				logging.info("MQTT client disconnected")
		
			# Stop CoAP server if enabled
			if self.coapServer:
				logging.info("Stopping CoAP server...")
				self.coapServer.stopServer()
				logging.info("CoAP server stopped")
		
			if self.sysPerfMgr:
				self.sysPerfMgr.stopManager()
				
			if self.sensorAdapterMgr:
				self.sensorAdapterMgr.stopManager()
    
			if self.executor:
					self.executor.shutdown(wait=True)
				
			logging.info("DeviceDataManager stopped successfully")
		except Exception as e:
			logging.error(f"Error stopping DeviceDataManager: {e}")
		
	def _handleIncomingDataAnalysis(self, msg: str):
		"""
		Call this from handleIncomeMessage() to determine if there's
		any action to take on the message. Steps to take:
		1) Validate msg: Most will be ActuatorData, but you may pass other info as well.
		2) Convert msg: Use DataUtil to convert if appropriate.
		3) Act on msg: Determine what - if any - action is required, and execute.
		"""
		logging.debug("Analyzing incoming message")
		
		try:
			# Attempt to convert JSON to ActuatorData
			actuatorData = self.dataUtil.jsonToActuatorData(msg)
			if actuatorData:
				self.handleActuatorCommandMessage(actuatorData)
		except Exception as e:
			logging.warning(f"Failed to process incoming message: {e}")
		
	def _handleSensorDataAnalysis(self, data: SensorData):
		"""
		Call this from handleSensorMessage() to determine if there's
		any action to take on the message.
		"""		
  	# 1. Humidity Analysis (New)
		if self.handleHumidityChangeOnDevice and data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE:
			logging.debug(f"Analyzing humidity: {data.getValue()}")
			
			actuatorData = ActuatorData(typeID=ConfigConst.HUMIDIFIER_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID())

			if data.getValue() < self.triggerHumidifierFloor:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHumidifierFloor) # Target Value
			elif data.getValue() > self.triggerHumidifierCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
			# Note: Logic can vary, typically humidifier turns ON when low, OFF when high/normal
			
			self.handleActuatorCommandMessage(actuatorData)
   
		# 2. Temperature Analysis (Existing logic, kept as is)
		elif self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.debug(f"Analyzing temperature: {data.getValue()}")
			
			actuatorData = ActuatorData(typeID=ConfigConst.HVAC_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID()) # Copy location
			
			if data.getValue() > self.triggerHvacTempCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHvacTempCeiling)
			elif data.getValue() < self.triggerHvacTempFloor:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHvacTempFloor)
			else:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
			
			self.handleActuatorCommandMessage(actuatorData)

		# 3. Pressure Analysis (New)
		elif self.handlePressureChangeOnDevice and data.getTypeID() == ConfigConst.PRESSURE_SENSOR_TYPE:
			logging.debug(f"Analyzing pressure: {data.getValue()}")
			
			# Using LED for pressure alarm (matches Java logic)
			actuatorData = ActuatorData(typeID=ConfigConst.LED_DISPLAY_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID())

			if data.getValue() < self.triggerPressureFloor or data.getValue() > self.triggerPressureCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(1.0) # LED ON
			else:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
				actuatorData.setValue(0.0) # LED OFF
			
			self.handleActuatorCommandMessage(actuatorData)

	def _executeUpstreamTransmission(self, resourceName: ResourceNameEnum, msg: str):
		"""
		This function contains the actual transmission logic and is designed
		to be run in a separate thread by the ThreadPoolExecutor to avoid deadlocks.
		"""
		logging.debug(f"Executing upstream transmission in thread for {resourceName}")
	
		# Track transmission results
		transmission_success = False
		
  		# MQTT transmission (if enabled)
		if self.mqttClient:
			try:
				success = self.mqttClient.publishMessage(
					resource=resourceName,
					msg=msg,
					qos=ConfigConst.DEFAULT_QOS
				)
				if success:
					logging.debug(f"Message published to MQTT topic: {resourceName.value}")
					transmission_success = True
				else:
					logging.warning(f"Failed to publish message to MQTT topic: {resourceName.value}")
			except Exception as e:
					logging.error(f"Error publishing to MQTT: {e}")
			
		# CoAP transmission (if enabled)
		if self.coapClient and self.coapClient.isConnected():
			try:
				if resourceName in [ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, 
														ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE]:
					success = self.coapClient.sendPostRequest(
						resource=resourceName,
						payload=msg
					)
				else:
					success = self.coapClient.sendPutRequest(
						resource=resourceName,
						payload=msg
					)
						
				if success:
					logging.debug(f"Message sent via CoAP to resource: {resourceName.value}")
					transmission_success = True
				else:
					logging.warning(f"Failed to send message via CoAP to resource: {resourceName.value}")
			except Exception as e:
				logging.error(f"Error sending via CoAP: {e}")
		
		if not transmission_success:
			logging.warning(f"No successful transmission for resource: {resourceName.value}")		
	
	def _handleUpstreamTransmission(self, resourceName: ResourceNameEnum, msg: str):
		"""
		Call this from handleActuatorCommandResponse(), handlesensorMessage(), and handleSystemPerformanceMessage()
		This method now submits the transmission task to a thread pool executor
		to avoid blocking the main (e.g., MQTT) thread.
		"""
		logging.debug(f"Submitting upstream transmission to executor for {resourceName}")
		
		# Submit the actual transmission logic to be run in a separate thread
		self.executor.submit(self._executeUpstreamTransmission, resourceName, msg)

	