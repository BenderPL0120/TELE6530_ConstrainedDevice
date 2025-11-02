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

from aiocoap.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData

class UpdateActuatorResourceHandler(Resource):
	"""
	Standard resource that will handle an incoming actuation command,
	and return the command response.
	
	This implementation extends from aiocoap's Resource base class.
	"""

	def __init__(self, name: str = ConfigConst.ACTUATOR_CMD,
	             dataMsgListener: IDataMessageListener = None):
		"""
		Constructor for UpdateActuatorResourceHandler
		
		@param name: The resource name (used for logging and identification)
		@param dataMsgListener: The data message listener for handling callbacks
		"""
		super().__init__()
		
		self.name = name
		
		# Get poll cycles configuration
		self.pollCycles = ConfigUtil().getInteger(
			section=ConfigConst.CONSTRAINED_DEVICE,
			key=ConfigConst.POLL_CYCLES_KEY,
			defaultVal=ConfigConst.DEFAULT_POLL_CYCLES)
		
		# Set expected content type to JSON
		self.expected_content_format = aiocoap.numbers.ContentFormat.JSON
		
		# Initialize data message listener and data utility
		self.dataMsgListener = dataMsgListener
		self.dataUtil = DataUtil()
		
		logging.info(f"Created UpdateActuatorResourceHandler for {name}")

	async def render_get(self, request):
		"""
		Handle GET request - returns current actuator status
		
		@param request: The CoAP request
		@return: CoAP response message
		"""
		logging.info(f"GET request received for Actuator resource: {self.name}")
		
		# For GET requests, return a simple status
		payload = f"Actuator resource '{self.name}' is available"
		
		response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload.encode('utf-8'))
		response.opt.content_format = aiocoap.numbers.ContentFormat.TEXT
		
		return response

	async def render_put(self, request):
		"""
		Handle PUT request - update actuator state with command
		
		@param request: The CoAP request containing actuator command
		@return: CoAP response message with actuator response data
		"""
		logging.info(f"PUT request received for Actuator resource: {self.name}")
		
		try:
			# Check if request is valid
			if not request:
				logging.error("PUT request is invalid (None)")
				response = aiocoap.Message(code=aiocoap.Code.INTERNAL_SERVER_ERROR)
				response.payload = b"Internal Server Error"
				return response
			
			# Check content-type
			if hasattr(request.opt, 'content_format'):
				if request.opt.content_format != self.expected_content_format:
					logging.warning(f"Unsupported content-type: {request.opt.content_format}. Must be application/json.")
					response = aiocoap.Message(code=aiocoap.Code.UNSUPPORTED_CONTENT_FORMAT)
					response.payload = b"Unsupported content-type. Must be application/json."
					return response
			
			# Check payload
			if not request.payload:
				logging.warning("No payload received in PUT request.")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"No payload received."
				return response
			
			# Try to convert payload to ActuatorData
			try:
				payloadStr = request.payload.decode('utf-8')
				logging.debug(f"Payload received: {payloadStr}")
				actuatorCmdData = self.dataUtil.jsonToActuatorData(payloadStr)
			except Exception as e:
				logging.error(f"Failed to decode payload: {e}")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"Invalid payload encoding."
				return response
			
			# Validate conversion result
			if not actuatorCmdData:
				logging.warning("Failed to parse ActuatorData from payload.")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"Invalid JSON format or data."
				return response
			
			# Create response with actuator data
			return self._createResponse(actuatorCmdData)
			
		except Exception as e:
			logging.error(f"Unexpected error handling PUT request: {e}")
			response = aiocoap.Message(code=aiocoap.Code.INTERNAL_SERVER_ERROR)
			response.payload = b"Internal Server Error"
			return response

	async def render_post(self, request):
		"""
		Handle POST request - create new actuator command
		
		@param request: The CoAP request containing actuator command
		@return: CoAP response message
		"""
		logging.info(f"POST request received for Actuator resource: {self.name}")
		
		try:
			# POST can use similar logic to PUT, but returns CREATED instead of CHANGED
			if not request.payload:
				logging.warning("No payload received in POST request.")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"No payload received."
				return response
			
			# Try to convert payload to ActuatorData
			try:
				payloadStr = request.payload.decode('utf-8')
				actuatorCmdData = self.dataUtil.jsonToActuatorData(payloadStr)
			except Exception as e:
				logging.error(f"Failed to decode payload: {e}")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"Invalid payload encoding."
				return response
			
			if not actuatorCmdData:
				logging.warning("Failed to parse ActuatorData from payload.")
				response = aiocoap.Message(code=aiocoap.Code.BAD_REQUEST)
				response.payload = b"Invalid JSON format or data."
				return response
			
			# Create response - use CREATED code for POST
			response = self._createResponse(actuatorCmdData)
			if response.code == aiocoap.Code.CHANGED:
				response.code = aiocoap.Code.CREATED
			
			return response
			
		except Exception as e:
			logging.error(f"Unexpected error handling POST request: {e}")
			response = aiocoap.Message(code=aiocoap.Code.INTERNAL_SERVER_ERROR)
			response.payload = b"Internal Server Error"
			return response

	async def render_delete(self, request):
		"""
		Handle DELETE request
		
		@param request: The CoAP request
		@return: CoAP response message
		"""
		logging.info(f"DELETE request received for Actuator resource: {self.name}")
		
		response = aiocoap.Message(code=aiocoap.Code.DELETED)
		response.payload = f"Actuator resource '{self.name}' deleted/reset".encode('utf-8')
		
		return response

	def _createResponse(self, data: ActuatorData = None) -> aiocoap.Message:
		"""
		Create response message with actuator response data
		
		@param data: The actuator command data to process
		@return: CoAP Message with appropriate response code and payload
		"""
		responseCode = aiocoap.Code.CHANGED
		actuatorResponseData = None
		
		try:
			# Check if we have a listener to handle the command
			if self.dataMsgListener:
				actuatorResponseData = self.dataMsgListener.handleActuatorCommandMessage(data)
			else:
				logging.warning("No data message listener configured.")
				actuatorResponseData = None
			
			# Check if command was processed successfully
			if not actuatorResponseData:
				logging.warning("Actuator command failed to be processed by listener.")
				
				# Create a failure response
				actuatorResponseData = ActuatorData()
				actuatorResponseData.updateData(data)
				actuatorResponseData.setAsResponse()
				actuatorResponseData.setStatusCode(-1)
				actuatorResponseData.setMessage("Failed to process actuator command.")
				
				responseCode = aiocoap.Code.PRECONDITION_FAILED
			else:
				logging.info("Actuator command processed successfully by listener.")
				responseCode = aiocoap.Code.CHANGED
			
			# Convert the response data to JSON
			jsonData = self.dataUtil.actuatorDataToJson(actuatorResponseData)
			logging.debug(f"Generated response: {jsonData}")
			
			# Create response message
			response = aiocoap.Message(code=responseCode, payload=jsonData.encode('utf-8'))
			response.opt.content_format = aiocoap.numbers.ContentFormat.JSON
			
			# Set max-age for caching
			response.opt.max_age = self.pollCycles
			
			return response
			
		except Exception as e:
			logging.error(f"Error creating response: {e}")
			response = aiocoap.Message(code=aiocoap.Code.INTERNAL_SERVER_ERROR)
			response.payload = b"Failed to create response"
			return response