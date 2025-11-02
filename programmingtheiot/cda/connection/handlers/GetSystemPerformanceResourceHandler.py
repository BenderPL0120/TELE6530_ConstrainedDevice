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
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener 

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class GetSystemPerformanceResourceHandler(ObservableResource, ISystemPerformanceDataListener):
	"""
	Observable resource that will collect system performance data based on the
	given name from the data message listener implementation.
	"""

	def __init__(self, name: str = ConfigConst.SYSTEM_PERF_MSG, 
				 dataMsgListener: IDataMessageListener = None):
		super().__init__()

		self.name = name
		self.pollCycles = \
			ConfigUtil().getInteger( \
				section = ConfigConst.CONSTRAINED_DEVICE, \
				key = ConfigConst.POLL_CYCLES_KEY, \
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)
		
		self.dataUtil = DataUtil()
		self.sysPerfData = None
		
		self.dataMsgListener = dataMsgListener
		
		# Register this handler as a listener if dataMsgListener is provided
		if self.dataMsgListener:
			self.dataMsgListener.setSystemPerformanceDataListener(self)
		
		# for testing
		self.payload = "GetSysPerfData"
		
	async def render_get(self, request):
		"""
		Handle GET request for system performance data
		"""
		responseCode = aiocoap.Code.CONTENT
		
		if not self.sysPerfData:
			self.sysPerfData = SystemPerformanceData()
			responseCode = aiocoap.Code.CONTENT
			
		jsonData = self.dataUtil.systemPerformanceDataToJson(self.sysPerfData)
		
		logging.info('Returning latest SystemPerformanceData: ' + jsonData)
		
		# Create response message
		response = aiocoap.Message(code=responseCode, payload=jsonData.encode('utf-8'))
		response.opt.content_format = aiocoap.numbers.ContentFormat.JSON
		
		# Set max-age for caching
		response.opt.max_age = self.pollCycles
		
		return response

	async def render_put(self, request):
		"""
		Handle PUT request
		"""
		logging.info("PUT request received for SystemPerformance resource")
		return aiocoap.Message(code=aiocoap.Code.CHANGED)
		
	async def render_post(self, request):
		"""
		Handle POST request
		"""
		logging.info("POST request received for SystemPerformance resource")
		return aiocoap.Message(code=aiocoap.Code.CREATED)
			
	async def render_delete(self, request):
		"""
		Handle DELETE request
		"""
		logging.info("DELETE request received for SystemPerformance resource")
		return aiocoap.Message(code=aiocoap.Code.DELETED)

	def onSystemPerformanceDataUpdate(self, data: SystemPerformanceData) -> bool:
		"""
		Callback method for system performance data updates
		"""
		self.sysPerfData = data
		
		# Notify observers that the resource has changed
		self.updated_state()
		
		return True
