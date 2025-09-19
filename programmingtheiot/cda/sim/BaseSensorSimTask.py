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

from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataSet

class BaseSensorSimTask():
	"""
	Shell representation of class for student implementation.
	
	"""

	DEFAULT_MIN_VAL = ConfigConst.DEFAULT_VAL
	DEFAULT_MAX_VAL = 1000.0
	
	def __init__(self, name = ConfigConst.NOT_SET, typeID: int = ConfigConst.DEFAULT_SENSOR_TYPE, dataSet = None, minVal: float = DEFAULT_MIN_VAL, maxVal: float = DEFAULT_MAX_VAL):
		self.name = name
		self.typeID = typeID
		self.dataSet = dataSet
		self.minVal = minVal
		self.maxVal = maxVal
		
		self.dataSetIndex = 0
		self.latestSensorData = None
		self.useRandomizer = (dataSet is None)
		
		# Validate min/max values
		if self.minVal > self.maxVal:
			self.minVal, self.maxVal = self.maxVal, self.minVal
		
		logging.info(f"Initialized {self.name} sensor simulator "
		           f"(mode: {'random' if self.useRandomizer else 'dataset'})")
	
	def generateTelemetry(self) -> SensorData:
		sensorData = SensorData(typeID=self.typeID, name=self.name)
		sensorVal = ConfigConst.DEFAULT_VAL
		
		if self.useRandomizer:
			sensorVal = random.uniform(self.minVal, self.maxVal)
		else:
			try:
				# handle SensorDataSet
				if hasattr(self.dataSet, 'getDataEntry'):
					sensorVal = self.dataSet.getDataEntry(index=self.dataSetIndex)
					dataSize = self.dataSet.getDataEntryCount()
				# handle list or tuple
				elif isinstance(self.dataSet, (list, tuple)):
					sensorVal = self.dataSet[self.dataSetIndex]
					dataSize = len(self.dataSet)
				else:
					raise TypeError(f"Unsupported dataset type: {type(self.dataSet)}")
				
				# loop the index
				self.dataSetIndex = (self.dataSetIndex + 1) % dataSize
					
			except (IndexError, AttributeError, TypeError) as e:
				logging.warning(f"Error reading dataset: {e}. Using default value.")
				sensorVal = ConfigConst.DEFAULT_VAL
		
		sensorData.setValue(sensorVal)
		self.latestSensorData = sensorData
		
		return self.latestSensorData
	
	def getTelemetryValue(self) -> float:
		"""
		If a local reference to SensorData is not None, simply return its current value.
		If SensorData hasn't yet been created, call self.generateTelemetry(), then return
		its current value.
		"""
		if self.latestSensorData is None:
			self.generateTelemetry()
		
		return self.latestSensorData.getValue()
	
	def getLatestTelemetry(self) -> SensorData:
		"""
		This can return the current SensorData instance or a copy.
		"""
		if self.latestSensorData is None:
			self.generateTelemetry()
		
		return self.latestSensorData
	
	def getName(self) -> str:
		return self.name
	
	def getTypeID(self) -> int:
		return self.typeID
	
	def _getDataSetSize(self):
			if hasattr(self, 'dataSet') and self.dataSet is not None:
					return len(self.dataSet)
			return 0
	