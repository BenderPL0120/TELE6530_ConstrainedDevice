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
from programmingtheiot.common.ConfigConst import BUZZER_ACTUATOR_TYPE

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

		# Initialize connection clients
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

		# Load Orientation control settings
		self.handleOrientationChangeOnDevice = self.configUtil.getBoolean(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.HANDLE_ORIENTATION_CHANGE_ON_DEVICE_KEY
		)
		self.triggerOrientationFloor = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.TRIGGER_ORIENTATION_FLOOR_KEY
		)
		self.triggerOrientationCeiling = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.TRIGGER_ORIENTATION_CEILING_KEY
		)

		# Load Magnetic control settings
		self.handleMagneticChangeOnDevice = self.configUtil.getBoolean(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.HANDLE_MAGNETIC_CHANGE_ON_DEVICE_KEY
		)
		self.triggerMagneticFloor = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.TRIGGER_MAGNETIC_FLOOR_KEY
		)
		self.triggerMagneticCeiling = self.configUtil.getFloat(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.TRIGGER_MAGNETIC_CEILING_KEY
		)

		# Actuator state tracking
		self.isHumidifierActive = True
		self.isPressureControlActive = True
		self.isHvacActive = True

		# Window state tracking
		self.isWindowOpen = False
		self.isWindowControlActive = True

		# Active alarm tracking
		# Stores actuator type IDs that are currently in an 'ON' (alarm) state
		self.activeAlarms = set()

		# safety defaults for orientation/magnetic
		# Yaw ∈ (-50, 50) => Straight Wind, Close
		# Pitch is a record of Window degrees
		# < -10 = Closed, > 50 = Open
		self.lastPitch = 0.0
		self.lastYaw = 180.0

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

			# 1. Humidity/Humidifier Control
			if data.getTypeID() == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE:
				if data.getCommand() == ConfigConst.COMMAND_ON:
					self.isHumidifierActive = True
					logging.info("Humidifier Logic ENABLED.")
				else:
					self.isHumidifierActive = False
					logging.info("Humidifier Logic DISABLED - Sensor data will be suppressed.")

			# 2. Pressure/LED Control
			elif data.getTypeID() == ConfigConst.LED_DISPLAY_ACTUATOR_TYPE:
				if data.getCommand() == ConfigConst.COMMAND_ON:
					self.isPressureControlActive = True
					logging.info("Pressure Control Logic ENABLED.")
				else:
					self.isPressureControlActive = False
					logging.info("Pressure Control Logic DISABLED - Sensor data will be suppressed.")

			# 3. Temperature/HVAC Control
			elif data.getTypeID() == ConfigConst.HVAC_ACTUATOR_TYPE:
				if data.getCommand() == ConfigConst.COMMAND_ON:
					self.isHvacActive = True
					logging.info("HVAC Logic ENABLED.")
				else:
					self.isHvacActive = False
					logging.info("HVAC Logic DISABLED - Sensor data will be suppressed.")

			# 4. Window Control
			elif data.getTypeID() == ConfigConst.WINDOW_ACTUATOR_TYPE:
				
				incomingCommand = data.getCommand()

				# [Safety Check] 
				# If the command is to OPEN the window, check local Yaw for unsafe wind.
				# We use 'lastYaw' because it is the most current local sensor reading.
				if incomingCommand == ConfigConst.COMMAND_ON:
					isUnsafeWind = (self.lastYaw > self.triggerMagneticFloor) and (self.lastYaw < self.triggerMagneticCeiling)
					
					if isUnsafeWind:
						logging.warning(f"SAFETY OVERRIDE: Cloud requested WINDOW OPEN, but local High Wind detected (Yaw: {self.lastYaw}). Command BLOCKED.")
						# Return None to stop processing. The window remains CLOSED.
						return None

				# [Deduplication]
				# Check if the incoming command matches the current state.
				# If the window is already CLOSED, ignore a CLOSE command (prevents redundant Buzzer/Logs).
				currentLocalState = ConfigConst.COMMAND_ON if self.isWindowOpen else ConfigConst.COMMAND_OFF
				
				if incomingCommand == currentLocalState:
					logging.info(f"Ignored duplicate Window command ({incomingCommand}). State is already matched.")
					return None

				# [Execution]
				# Update the state and log the action
				if incomingCommand == ConfigConst.COMMAND_ON:
					self.isWindowOpen = True
					logging.info("Window OPENED.")
				else:
					self.isWindowOpen = False
					logging.info("Window CLOSED.")
				
				# [Buzzer Sync]
				# Trigger the sound alert to match the window action.
				# True = Open Sound, False = Close Sound
				self._triggerSoundAlert(self.isWindowOpen, data.getLocationID())

			# 5. Buzzer Control (Handling remote commands from GDA)
			elif data.getTypeID() == ConfigConst.BUZZER_ACTUATOR_TYPE:
				logging.info(f"Received remote Buzzer command: {data.getCommand()}")

			return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Received invalid ActuatorData command message. Ignoring.")
			return None

	def handleActuatorCommandResponse(self, data: ActuatorData) -> bool:
		if data:
			logging.debug(f"Actuator response received: {data}")

			self.actuatorResponseCache[data.getName()] = data

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

			self.sensorDataCache[data.getName()] = data

			self._handleSensorDataAnalysis(data)

			shouldSendUpstream = True

			# 1. Check humidity
			if data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE:
				if not self.isHumidifierActive:
					logging.debug("Humidifier logic is OFF. Suppressing humidity upload.")
					shouldSendUpstream = False

			# 2. Check temperature
			elif data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
				if not self.isHvacActive:
					logging.debug("HVAC logic is OFF. Suppressing temp upload.")
					shouldSendUpstream = False

			# 3. Check pressure
			elif data.getTypeID() == ConfigConst.PRESSURE_SENSOR_TYPE:
				if not self.isPressureControlActive:
					logging.debug("Pressure Control Logic is OFF. Suppressing pressure upload.")
					shouldSendUpstream = False

			# 4. Check orientation
			elif data.getTypeID() == ConfigConst.ORIENTATION_SENSOR_TYPE:
				if not self.isWindowControlActive:
					logging.debug("Window Control Logic is OFF. Suppressing orientation upload.")
					shouldSendUpstream = False

			# 5. Check magnetic
			elif data.getTypeID() == ConfigConst.MAGNETIC_SENSOR_TYPE:
				if not self.isWindowControlActive:
					logging.debug("Window Control Logic is OFF. Suppressing magnetic upload.")
					shouldSendUpstream = False

			if shouldSendUpstream:
				sensorMsg = self.dataUtil.sensorDataToJson(data)
				resourceName = ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE
				self._handleUpstreamTransmission(resourceName=resourceName, msg=sensorMsg)
			else:
				logging.info(f"Data upload suppressed for {data.getName()} due to actuator state.")

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

			self.sysPerfDataCache[data.getName()] = data

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

			if self.mqttClient:
				logging.info("Connecting MQTT client...")
				self.mqttClient.connectClient()

			if self.coapServer:
				logging.info("Starting CoAP server...")
				self.coapServer.startServer()
				logging.info("CoAP server started")
				
			self._initActuatorState()
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
			if self.mqttClient:
				logging.info("Disconnecting MQTT client...")
				self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
				self.mqttClient.disconnectClient()
				logging.info("MQTT client disconnected")

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

	def _initActuatorState(self):
		"""
		Initialize the actuators to a default safe state on startup.
		For example, ensure the Window is CLOSED.
		"""
		logging.info("Initializing actuator states to default...")

		# 1. Force Window CLOSED
		# Create a local ActuatorData command
		windowData = ActuatorData(typeID=ConfigConst.WINDOW_ACTUATOR_TYPE)
		windowData.setCommand(ConfigConst.COMMAND_OFF)
		windowData.setStateData("Initialization: Window Closed")
		windowData.setValue(0.0)

		# Send directly to ActuatorAdapterManager (bypassing MQTT/CoAP logic)
		if self.actuatorAdapterMgr:
			self.actuatorAdapterMgr.sendActuatorCommand(windowData)

		# Ensure internal state matches
		self.isWindowOpen = False

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

	def _updateAlarmState(self, actuatorType: int, isActive: bool, locationID: str):
		"""
		Updates the set of active alarms. If 'isActive' is True, the actuator type is added.
		If False, it is removed.

		If the set becomes empty (all alarms cleared), this triggers a refresh of the
		Window display to restore its status.
		"""
		wasAlarming = len(self.activeAlarms) > 0

		if isActive:
			self.activeAlarms.add(actuatorType)
		else:
			if actuatorType in self.activeAlarms:
				self.activeAlarms.remove(actuatorType)

		isAlarming = len(self.activeAlarms) > 0

		# If alarms were active but now are all cleared, restore the default window display
		if wasAlarming and not isAlarming:
			logging.info(f"All alarms cleared (Type {actuatorType} ended). Restoring Window display.")
			self._refreshWindowDisplay(locationID)

	def _refreshWindowDisplay(self, locationID: str):
		"""
		Restores the Window display on the LED matrix.
		This is called when high-priority alarms (like Pressure or HVAC) are cleared,
		allowing the Window status (Open/Closed) to be shown again.
		"""
		if not self.handleOrientationChangeOnDevice:
			return

		logging.debug("Refreshing window display state.")

		# Construct a command based on the current internal state
		restoreMsg = ActuatorData(typeID=ConfigConst.WINDOW_ACTUATOR_TYPE)
		restoreMsg.setLocationID(locationID)

		if self.isWindowOpen:
			restoreMsg.setCommand(ConfigConst.COMMAND_ON)
			restoreMsg.setStateData("WINDOW_OPEN")
		else:
			restoreMsg.setCommand(ConfigConst.COMMAND_OFF)
			restoreMsg.setStateData("WINDOW_CLOSED")

		# Send directly to the adapter manager, bypassing handleActuatorCommandMessage
		# to avoid redundant logic processing.
		if self.actuatorAdapterMgr:
			self.actuatorAdapterMgr.sendActuatorCommand(restoreMsg)

	def _handleSensorDataAnalysis(self, data: SensorData):
		"""
		Analyzes sensor data to trigger local actuation logic.

		Design Principle:
		The Window Display (controlled by Orientation) is the Lowest Priority.
		Any other Actuator entering an 'ON' state (Humidifier, HVAC, LED Alarm)
		will suppress the Window Display until the alarm condition clears.
		"""

		# 1. Humidity Analysis
		if self.handleHumidityChangeOnDevice and data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE:
			logging.debug(f"Analyzing humidity: {data.getValue()}")

			actuatorData = ActuatorData(typeID=ConfigConst.HUMIDIFIER_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID())

			isTriggered = False

			if data.getValue() < self.triggerHumidifierFloor:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHumidifierFloor)
				isTriggered = True
			elif data.getValue() > self.triggerHumidifierCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
				actuatorData.setValue(data.getValue())
				isTriggered = False

			# Only send command if a state change is explicitly detected (ON or OFF)
			# to respect hysteresis.
			if actuatorData.getCommand() != ConfigConst.DEFAULT_COMMAND:
				self.handleActuatorCommandMessage(actuatorData)
				# Update alarm state based on command sent
				self._updateAlarmState(ConfigConst.HUMIDIFIER_ACTUATOR_TYPE, isTriggered, data.getLocationID())

		# 2. Temperature Analysis
		elif self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.debug(f"Analyzing temperature: {data.getValue()}")

			actuatorData = ActuatorData(typeID=ConfigConst.HVAC_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID())

			isTriggered = False

			if data.getValue() > self.triggerHvacTempCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHvacTempCeiling)
				isTriggered = True
			elif data.getValue() < self.triggerHvacTempFloor:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(self.triggerHvacTempFloor)
				isTriggered = True
			else:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
				isTriggered = False

			self.handleActuatorCommandMessage(actuatorData)
			self._updateAlarmState(ConfigConst.HVAC_ACTUATOR_TYPE, isTriggered, data.getLocationID())

		# 3. Pressure Analysis
		elif self.handlePressureChangeOnDevice and data.getTypeID() == ConfigConst.PRESSURE_SENSOR_TYPE:
			logging.debug(f"Analyzing pressure: {data.getValue()}")

			actuatorData = ActuatorData(typeID=ConfigConst.LED_DISPLAY_ACTUATOR_TYPE)
			actuatorData.setLocationID(data.getLocationID())

			isTriggered = False

			if data.getValue() < self.triggerPressureFloor or data.getValue() > self.triggerPressureCeiling:
				actuatorData.setCommand(ConfigConst.COMMAND_ON)
				actuatorData.setValue(1.0)
				isTriggered = True
			else:
				actuatorData.setCommand(ConfigConst.COMMAND_OFF)
				actuatorData.setValue(0.0)
				isTriggered = False

			self.handleActuatorCommandMessage(actuatorData)
			self._updateAlarmState(ConfigConst.LED_DISPLAY_ACTUATOR_TYPE, isTriggered, data.getLocationID())

		# 4. Orientation Analysis - Controls Window Actuator (Lowest Priority)
		elif self.handleOrientationChangeOnDevice and data.getTypeID() == ConfigConst.ORIENTATION_SENSOR_TYPE:
			logging.debug(f"Updating Pitch: {data.getValue()}")
			self.lastPitch = data.getValue()
			self._evaluateAndActuateWindow(data.getLocationID())

		# 5. Magnetic Analysis - Controls Window Actuator (Lowest Priority)
		elif self.handleMagneticChangeOnDevice and data.getTypeID() == ConfigConst.MAGNETIC_SENSOR_TYPE:
			logging.debug(f"Updating Yaw: {data.getValue()}")
			self.lastYaw = data.getValue()
			self._evaluateAndActuateWindow(data.getLocationID())

	def _executeUpstreamTransmission(self, resourceName: ResourceNameEnum, msg: str):
		"""
		This function contains the actual transmission logic and is designed
		to be run in a separate thread by the ThreadPoolExecutor to avoid deadlocks.
		"""
		logging.debug(f"Executing upstream transmission in thread for {resourceName}")

		transmission_success = False

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

		self.executor.submit(self._executeUpstreamTransmission, resourceName, msg)

	def _triggerSoundAlert(self, isOpenAction: bool, locationID: str):
		"""
		Helper to send command to Sound Actuator
		isOpenAction=True -> Play Open Sound
		isOpenAction=False -> Play Close Sound
		"""
		if self.actuatorAdapterMgr:
			buzzerData = ActuatorData(typeID=BUZZER_ACTUATOR_TYPE)
			buzzerData.setLocationID(locationID)

			if isOpenAction:
				buzzerData.setCommand(ConfigConst.COMMAND_ON)
			else:
				buzzerData.setCommand(ConfigConst.COMMAND_OFF)

			self.actuatorAdapterMgr.sendActuatorCommand(buzzerData)

	def _evaluateAndActuateWindow(self, locationID: str):
		"""
		Comprehensively control the window based on Pitch (User Intent) and Yaw (Environmental Wind Constraint).

		Logic Design:
		1. Yaw between (-50, 50) -> Simulates cold wind blowing directly, force window CLOSE (Highest Priority).
		2. Yaw in safe zone -> Allow Pitch to control window toggle.
		"""
		# If relevant sensor logic is not enabled, return immediately
		if not self.handleOrientationChangeOnDevice and not self.handleMagneticChangeOnDevice:
			return

		targetCommand = None
		targetStateData = None

		# --- Logic Layer 1: Check Yaw (Environmental Constraint/Cold Wind) ---
		# In config: Floor = -50.0, Ceiling = 50.0
		isColdWind = (self.lastYaw > self.triggerMagneticFloor) and (self.lastYaw < self.triggerMagneticCeiling)

		if isColdWind:
			# Regardless of what the Pitch is, the window must be closed
			logging.info(f"Wind Condition Detected (Yaw: {self.lastYaw}): Forcing Window CLOSE.")
			targetCommand = ConfigConst.COMMAND_OFF
			targetStateData = "WINDOW_CLOSED"

		# --- Logic Layer 2: Check Pitch (Open/Close Control) ---
		else:
			# Environment is safe, allow Pitch control
			# In config: Floor = -10.0, Ceiling = 50.0
			if self.lastPitch > self.triggerOrientationCeiling:
				# Pitch > 50 -> Open Window
				targetCommand = ConfigConst.COMMAND_ON
				targetStateData = "WINDOW_OPEN"
			elif self.lastPitch < self.triggerOrientationFloor:
				# Pitch < -10 -> Close Window
				targetCommand = ConfigConst.COMMAND_OFF
				targetStateData = "WINDOW_CLOSED"
		# Otherwise maintain current state (Hysteresis)

		# --- Execution Layer ---
		# Execute only if a clear target command is calculated AND it changes the current state
		if targetCommand is not None:
			# Check if state has changed
			isCommandOpen = (targetCommand == ConfigConst.COMMAND_ON)
			if self.isWindowOpen != isCommandOpen:

				# Prepare to send command
				actuatorData = ActuatorData(typeID=ConfigConst.WINDOW_ACTUATOR_TYPE)
				actuatorData.setLocationID(locationID)
				actuatorData.setCommand(targetCommand)
				actuatorData.setStateData(targetStateData)

				# Update internal state
				self.isWindowOpen = isCommandOpen

				# Trigger sound alert (True=Open Sound, False=Close Sound)
				self._triggerSoundAlert(self.isWindowOpen, locationID)

				# Check if higher priority system alarms (e.g., Fire/Pressure) are suppressing the actuation
				if len(self.activeAlarms) > 0:
					logging.debug(f"Window actuation suppressed by active alarms: {self.activeAlarms}")
				else:
					# Send command to actuator
					self.handleActuatorCommandMessage(actuatorData)