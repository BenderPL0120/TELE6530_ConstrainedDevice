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
import aiocoap

from aiocoap.resource import ObservableResource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SensorData import SensorData

class GetTelemetryResourceHandler(ObservableResource, ITelemetryDataListener):
	"""
	Observable resource that will collect telemetry based on the given
	name from the data message listener implementation.
	"""

	def __init__(self, name: str = ConfigConst.SENSOR_MSG,
				 dataMsgListener: IDataMessageListener = None):
		super().__init__()
		
		self.name = name
		self.pollCycles = \
			ConfigUtil().getInteger( \
				section = ConfigConst.CONSTRAINED_DEVICE, \
				key = ConfigConst.POLL_CYCLES_KEY, \
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)
		
		self.dataUtil = DataUtil()
		self.sensorData = None
		
		self.dataMsgListener = dataMsgListener
		
		# Register this handler as a listener if dataMsgListener is provided
		if self.dataMsgListener:
			self.dataMsgListener.setTelemetryDataListener(self)
		
		# for testing
		self.payload = "GetSensorData"
		
	async def render_get(self, request):
		"""
		Handle GET request for telemetry data
		"""
		responseCode = aiocoap.Code.CONTENT
		
		if not self.sensorData:
			self.sensorData = SensorData()
			responseCode = aiocoap.Code.CONTENT
			
		jsonData = self.dataUtil.sensorDataToJson(self.sensorData)
		
		logging.info('Returning latest SensorData: ' + jsonData)
		
		# Create response message
		response = aiocoap.Message(code=responseCode, payload=jsonData.encode('utf-8'))
		response.opt.content_format = aiocoap.numbers.ContentFormat.JSON
		
		# Set max-age for caching
		response.opt.max_age = self.pollCycles
		
		return response

	def onSensorDataUpdate(self, data: SensorData = None) -> bool:
		"""
		Callback method for sensor data updates
		"""
		if data:
			self.sensorData = data
			
			# Notify observers that the resource has changed
			self.updated_state()
			
			return True
		return False