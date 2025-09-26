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

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.BaseIotData import BaseIotData

class SensorData(BaseIotData):
	"""
	Shell representation of class for student implementation.
	
	"""
		
	def __init__(self, typeID: int = ConfigConst.DEFAULT_SENSOR_TYPE, name = ConfigConst.NOT_SET, d = None):
		super(SensorData, self).__init__(name = name, typeID = typeID, d = d)
		# Initialize instance variables with defaults
		self.value = ConfigConst.DEFAULT_VAL
		
		# If initialization data provided, update from it
		if d is not None:
			self._handleUpdateData(d)
	
	def getSensorType(self) -> int:
		"""
		Returns the sensor type to the caller.
		
		@return int
		"""
		return self.sensorType
	
	def getValue(self) -> float:
		return self.value
	
	def setValue(self, newVal: float):
		if newVal is not None:
			self.value = float(newVal)
			self.updateTimeStamp()

	def __str__(self) -> str:
		"""
		Override the base class __str__ to include the value field.
		"""
		base_str = super().__str__()
		# Add the value field
		return f"{base_str},value={self.value}"
		
	def _handleUpdateData(self, data):
		try:
			if data and isinstance(data, SensorData):
				self.value = data.getValue()
			elif data and isinstance(data, dict):
				self.value = data.get('value', self.value)
		except Exception as e:
			print("SensorData: Unexpected error in _handleUpdateData: " + str(e))
			pass