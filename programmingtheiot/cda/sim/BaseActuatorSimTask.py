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
import random

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.ActuatorData import ActuatorData

class BaseActuatorSimTask():
	"""
	Shell representation of class for student implementation.
	
	"""

	def __init__(self, name: str = ConfigConst.NOT_SET, typeID: int = ConfigConst.DEFAULT_ACTUATOR_TYPE, simpleName: str = "Actuator"):
		self.name = name
		self.typeID = typeID
		self.simpleName = simpleName
		
		self.latestActuatorResponse = ActuatorData(typeID = self.typeID, name = self.name)
		self.latestActuatorResponse.setAsResponse()
		
		self.lastKnownCommand = ConfigConst.DEFAULT_COMMAND
		self.lastKnownValue = ConfigConst.DEFAULT_VAL
		
		logging.info(f"Initialized {self.simpleName} actuator simulator: {self.name}")
		
	def getLatestActuatorResponse(self) -> ActuatorData:
		"""
		This can return the current ActuatorData response instance or a copy.
		"""
		return self.latestActuatorResponse
	
	def getSimpleName(self) -> str:
		return self.simpleName
	
	def updateActuator(self, data: ActuatorData) -> bool:
		"""
		NOTE: If 'data' is valid, the actuator-specific work can be delegated
		as follows:
		 - if command is ON: call self._activateActuator()
		 - if command is OFF: call self._deactivateActuator()
		
		Both of these methods will have a generic implementation (logging only) within
		this base class, although the sub-class may override if preferable.
		"""
		# Validate the incoming ActuatorData object and its typeID
		if data and self.typeID == data.getTypeID():
			statusCode = ConfigConst.DEFAULT_STATUS
			
			curCommand = data.getCommand()
			curVal     = data.getValue()
			
			# Check if the command is a repeat of the last one; if so, ignore.
			if curCommand == self.lastKnownCommand and curVal == self.lastKnownValue:
				# Always process OFF commands even if they are repeats
				if curCommand != ConfigConst.COMMAND_OFF:
					logging.debug(f"New actuator command is a repeat. Ignoring: CMD={curCommand}, VAL={curVal}")
					return None
				else:
					logging.debug(f"OFF command received - executing despite repeat")
				
			# Delegate to the appropriate handler
			if curCommand == ConfigConst.COMMAND_ON:
				logging.info("Activating actuator...")
				statusCode = self._activateActuator(val = data.getValue(), stateData = data.getStateData())
			elif curCommand == ConfigConst.COMMAND_OFF:
				logging.info("Deactivating actuator...")
				statusCode = self._deactivateActuator(val = data.getValue(), stateData = data.getStateData())
			else:
				logging.warning(f"ActuatorData command is unknown. Ignoring: {curCommand}")
				statusCode = -1
				
			# Update the last known state
			self.lastKnownCommand = curCommand
			self.lastKnownValue = curVal
			
			# Create the response object from the original command
			actuatorResponse = ActuatorData()
			actuatorResponse.updateData(data)
			actuatorResponse.setStatusCode(statusCode)
			actuatorResponse.setAsResponse()
			
			self.latestActuatorResponse.updateData(actuatorResponse)
			
			return actuatorResponse
		
		# Return None if data is invalid
		return None
	
	def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		"""
		Implement basic logging. Actuator-specific functionality should be implemented by sub-class.
		
		@param val The actuation activation value to process.
		@param stateData The string state data to use in processing the command.
		"""
		msg = "\n*******"
		msg += "\n* O N *"
		msg += "\n*******"
		msg += f"\n{self.name} VALUE -> {val}\n======="
			
		logging.info(f"Simulating {self.name} actuator ON: {msg}")
		
		return 0
		
	def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		"""
		Implement basic logging. Actuator-specific functionality should be implemented by sub-class.
		
		@param val The actuation activation value to process.
		@param stateData The string state data to use in processing the command.
		"""
		msg = "\n*******"
		msg += "\n* OFF *"
		msg += "\n*******"
		
		logging.info(f"Simulating {self.name} actuator OFF: {msg}")
				
		return 0
		