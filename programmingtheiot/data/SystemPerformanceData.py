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

class SystemPerformanceData(BaseIotData):
	"""
	Shell representation of class for student implementation.
	
	"""
	DEFAULT_VAL = 0.0
	
	def __init__(self, d = None):
		super(SystemPerformanceData, self).__init__(name = ConfigConst.SYSTEM_PERF_MSG, typeID = ConfigConst.SYSTEM_PERF_TYPE, d = d)
		# Initialize instance variables with defaults
		self.cpuUtil = ConfigConst.DEFAULT_VAL
		self.memUtil = ConfigConst.DEFAULT_VAL
		self.diskUtil = ConfigConst.DEFAULT_VAL

		# If initialization data provided, update from it
		if d is not None:
			self._handleUpdateData(d)
	
	def getCpuUtilization(self):
		return self.cpuUtil
	
	def getDiskUtilization(self):
		return self.diskUtil
	
	def getMemoryUtilization(self):
		return self.memUtil

	def setCpuUtilization(self, cpuUtil):
		if cpuUtil is not None:
			self.cpuUtil = self._clampUtilization(cpuUtil)
			self.updateTimeStamp()
	
	def setDiskUtilization(self, diskUtil):
		if diskUtil is not None:
			self.diskUtil = self._clampUtilization(diskUtil)
			self.updateTimeStamp()
	
	def setMemoryUtilization(self, memUtil):
		if memUtil is not None:
			self.memUtil = self._clampUtilization(memUtil)
			self.updateTimeStamp()

	def _clampUtilization(self, value: float) -> float:
		"""
		Ensure utilization values stay within 0-100 range.
		"""
		return max(0.0, min(100.0, float(value)))
	
	def _handleUpdateData(self, data):
		try:
			if data and isinstance(data, SystemPerformanceData):
				self.cpuUtil = data.getCpuUtilization()
				self.memUtil = data.getMemoryUtilization()
				self.diskUtil = data.getDiskUtilization()
			elif data and isinstance(data, dict):
				self.cpuUtil = data.get('cpuUtil', self.cpuUtil)
				self.memUtil = data.get('memUtil', self.memUtil)
				self.diskUtil = data.get('diskUtil', self.diskUtil)
		except Exception as e:
			print("SystemPerformanceData: Unexpected error in _handleUpdateData: " + str(e))
			pass
