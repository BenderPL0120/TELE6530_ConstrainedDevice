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

from importlib import import_module

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.ActuatorData import ActuatorData

from programmingtheiot.cda.sim.HvacActuatorSimTask import HvacActuatorSimTask
from programmingtheiot.cda.sim.HumidifierActuatorSimTask import HumidifierActuatorSimTask

class ActuatorAdapterManager(object):
	"""
	Shell representation of class for student implementation.
	
	"""
	
	def __init__(self, dataMsgListener: IDataMessageListener = None):
		"""
		Constructor for ActuatorAdapterManager.
		"""
		self.configUtil = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		
		self.useEmulator = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_EMULATOR_KEY)
			
		self.locationID = self.configUtil.getProperty(
			section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.DEVICE_LOCATION_ID_KEY, defaultVal=ConfigConst.NOT_SET)
		
		self.deviceID = self.configUtil.getProperty(
    	section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.DEVICE_ID_KEY, defaultVal=ConfigConst.NOT_SET)

		self.humidifierActuator = None
		self.hvacActuator = None
		self.ledDisplayActuator = None # Placeholder for future actuators
		
		# Log the operational mode
		if self.useEmulator:
			logging.info("Emulators will be used for actuators.")
		else:
			logging.info("Simulators will be used for actuators.")
			
		# Encapsulate actuator task creation
		self._initEnvironmentalActuationTasks()

	def sendActuatorCommand(self, data: ActuatorData) -> ActuatorData:
		"""
		Receives an ActuatorData command, validates it, and dispatches it to the correct actuator.
		"""
		# GATEWAY: Validate the incoming command
		if not data or data.isResponseFlagEnabled():
			logging.warning("Invalid ActuatorData received. Ignoring.")
			return None
		
		# GATEWAY: Check if the command is intended for this device's location
		if data.getLocationID() != self.locationID:
			logging.warning(
				"Location ID mismatch. Ignoring actuation command. Expected: %s, Got: %s",
				self.locationID, data.getLocationID())
			return None
			
		logging.info(
			"Actuator command received for location ID %s. Processing...", self.locationID)
		
		# HUB: Dispatch the command to the appropriate actuator
		actuatorType = data.getTypeID()
		responseData = None
		
		if actuatorType == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE and self.humidifierActuator:
			responseData = self.humidifierActuator.updateActuator(data)
		elif actuatorType == ConfigConst.HVAC_ACTUATOR_TYPE and self.hvacActuator:
			responseData = self.hvacActuator.updateActuator(data)
		# elif actuatorType == ConfigConst.LED_DISPLAY_ACTUATOR_TYPE and self.ledDisplayActuator:
		#	responseData = self.ledDisplayActuator.updateActuator(data)
		else:
			logging.error(
				"No valid actuator found for type ID: %s. Command ignored.", str(actuatorType))
			
		# NOTE: In a future implementation, this responseData could be passed
		# to the dataMsgListener to notify other components.
		# if self.dataMsgListener and responseData:
		#     self.dataMsgListener.handleActuatorMessage(responseData)
			
		return responseData
	
	def setDataMessageListener(self, listener: IDataMessageListener) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		return False

	def _initEnvironmentalActuationTasks(self):
		"""
		Private helper method to initialize actuator tasks based on configuration.
		"""
		if not self.useEmulator:
			# Load the environmental tasks for simulated actuation
			logging.info("Initializing simulated environmental actuators...")
			self.humidifierActuator = HumidifierActuatorSimTask()
			self.hvacActuator = HvacActuatorSimTask()
		else:
			# Load the environmental tasks for emulated actuation
			logging.info("Initializing emulated environmental actuators...")
			# TODO: Add emulator implementation logic here
			pass
