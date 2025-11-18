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
import socket
import threading
import traceback

import asyncio

from aiocoap import *
from contextlib import suppress

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

from programmingtheiot.data.DataUtil import DataUtil

class CoapClientConnector(IRequestResponseClient):
	"""
	CoAP Client implementation using aiocoap library
	"""
	
	def __init__(self, dataMsgListener: IDataMessageListener = None):
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		self.coapClient = None
		
		self.observeRequests = { }
		self.observeTasks = { }
		
		self.host = self.config.getProperty(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		self.port = self.config.getInteger(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_COAP_PORT)
		
		self.includeDebugLogDetail = True
		
		try:
			tmpHost = socket.gethostbyname(self.host)
			
			if tmpHost:
				self.host = tmpHost
				self.uriPath = f"coap://{self.host}:{self.port}/"
				logging.info(f"CoAP client will connect to: {self.uriPath}")
				self._initEventLoop()
			else:
				logging.error(f"Can't resolve host: {self.host}")
				raise
			
		except socket.gaierror:
			logging.error(f"Failed to resolve host: {self.host}. Check hostname in config.")
			raise
	
	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		"""Set data message listener"""
		if listener:
			self.dataMsgListener = listener
			return True
		
		return False
	
	def _createResourcePath(self, resource: ResourceNameEnum = None, name: str = None):
		"""Create resource path from resource enum and name"""
		resourcePath = ""
		hasResource = False
		
		if resource:
			resourcePath = resourcePath + resource.value
			hasResource = True
			
		if name:
			if hasResource:
				resourcePath = resourcePath + "/"
			
			resourcePath = resourcePath + name
		
		return resourcePath

	# Async handlers for CoAP methods
	async def _handleStartObserveRequest(self, resourcePath: str = None):
		"""Handle start observe request"""
		logging.info(f"Handle start observe invoked. Waiting for each input: {resourcePath}")
		
		try:
			msg = Message(code = Code.GET, uri = resourcePath, observe = 0)
			req = self.clientContext.request(msg)

			# store with relative path as key
			# needed for later cleanup
			relativePath = resourcePath.replace(self.uriPath, "")
			self.observeRequests[relativePath] = req

			# get initial response
			responseData = await req.response
			self._onGetResponse(responseData)
			
			# continue observation
			async for responseData in req.observation:
				self._onGetResponse(responseData)
				
		except asyncio.CancelledError:
			# expected
			logging.info(f"Observation cancelled for {resourcePath}")

		except Exception as e:
			logging.warning(f"Failed to execute OBSERVE - GET. Error: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)

		finally:
			relativePath = resourcePath.replace(self.uriPath, "")

			if relativePath in self.observeRequests:
				del self.observeRequests[relativePath]
	
	async def _handleStopObserveRequest(self, resourcePath: str = None, ignoreErr: bool = False):
		"""Handle stop observe request"""
		if resourcePath in self.observeRequests:
			logging.info(f"Handle stop observe invoked: {resourcePath}")

			try:
				observeRequest = self.observeRequests[resourcePath]
				observeRequest.observation.cancel()

			except Exception as e:
				if not ignoreErr:
					logging.warning(f"Failed to cancel OBSERVE - GET: {resourcePath}")

			try:
				del self.observeRequests[resourcePath]

			except Exception as e:
				if not ignoreErr:
					logging.warning(f"Failed to remove observable from list: {resourcePath}")

		else:
			if not ignoreErr:
				logging.warning(f"Resource not currently under observation. Ignoring: {resourcePath}")
	
	async def _handleDeleteRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""Handle DELETE request"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
	
			msgType = NON
			
			if enableCON:
				msgType = CON
				
			msg = Message(mtype = msgType, code = Code.DELETE, uri = uriAndResourcePath)

			responseData = await self.clientContext.request(request_message = msg).response
			
			self._onDeleteResponse(responseData)
			
		except Exception as e:
			logging.warning(f"Failed to process Async DELETE request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
	
	async def _handleDiscoveryRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""Handle Discovery request"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
	
			msgType = NON
			
			if enableCON:
				msgType = CON
				
			msg = Message(mtype = msgType, code = Code.GET, uri = uriAndResourcePath)

			responseData = await self.clientContext.request(request_message = msg).response
			
			self._onDiscoveryResponse(responseData)

		except Exception as e:
			logging.warning(f"Failed to process Async DISCOVERY request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
	
	async def _handleGetRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""Handle GET request"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
	
			msgType = NON
			
			if enableCON:
				msgType = CON
				
			msg = Message(mtype = msgType, code = Code.GET, uri = uriAndResourcePath)

			responseData = await self.clientContext.request(request_message = msg).response
			
			self._onGetResponse(responseData)

		except Exception as e:
			logging.warning(f"Failed to process Async GET request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
	
	async def _handlePostRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		"""Handle POST request"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
	
			msgType = NON
			
			if enableCON:
				msgType = CON
				
			msg = Message(mtype = msgType, payload = payload.encode("utf-8"), code = Code.POST, uri = uriAndResourcePath)

			responseData = await self.clientContext.request(request_message = msg).response
			
			self._onPostResponse(responseData)

		except Exception as e:
			logging.warning(f"Failed to process Async POST request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
	
	async def _shutdownClient(self):
		"""
		Internal async method to shut down the client context.
		"""
		try:
			# Cancel any pending observe tasks
			logging.debug("Cancelling observe tasks...")
			for task in self.observeTasks.values():
				if task and not task.done():
					task.cancel()
					with suppress(asyncio.CancelledError):
						await task
			
			self.observeTasks.clear()
			self.observeRequests.clear()

			if self.clientContext:
				logging.info("Shutting down CoAP client context...")
				await self.clientContext.shutdown()
				self.clientContext = None
				logging.info("CoAP client context shut down.")

		except Exception as e:
			logging.warning(f"Failed to shut down CoAP client context cleanly: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)
  
	async def _handlePutRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		"""Handle PUT request"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
	
			msgType = NON
			
			if enableCON:
				msgType = CON
				
			msg = Message(mtype = msgType, payload = payload.encode("utf-8"), code = Code.PUT, uri = uriAndResourcePath)

			responseData = await self.clientContext.request(request_message = msg).response
			
			self._onPutResponse(responseData)
			
		except Exception as e:
			logging.warning(f"Failed to process Async PUT request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)

	# Response handling methods
	def _onDeleteResponse(self, response):
		"""Handle DELETE response"""
		if not response:
			logging.warning("Async DELETE response invalid. Ignoring.")
			return
		
		logging.info("Async DELETE response received.")
		
		responseData = response.payload.decode("utf-8")
		
		logging.info(f"Response data received. Payload: {responseData}")
	
	def _onDiscoveryResponse(self, response):
		"""Handle Discovery response"""
		if not response:
			logging.warning("Async GET - DISCOVERY response invalid. Ignoring.")
			return
		
		logging.info("Async GET - DISCOVERY response received.")
		
		if len(response.requested_path) >= 2:
			logging.info("Resources: " + str(response.payload))
		else:
			logging.info("Response: " + str(response))
	
	def _onGetResponse(self, response):
		"""Handle GET response"""
		if not response:
			logging.warning("Async GET response invalid. Ignoring.")
			return
		
		logging.info("Async GET response received.")
		
		jsonData = response.payload.decode("utf-8")
		
		if len(response.requested_path) >= 2:
			logging.info(f"Response: {response.requested_path}")
			
			dataType = response.requested_path[1]
			
			if dataType == ConfigConst.ACTUATOR_CMD:
				# convert payload to ActuatorData and verify
				logging.info(f"ActuatorData received: {jsonData}")
				
				try:
					ad = DataUtil().jsonToActuatorData(jsonData)
					
					if self.dataMsgListener:
						self.dataMsgListener.handleActuatorCommandMessage(ad)
				except:
					logging.warning(f"Failed to decode actuator data. Ignoring: : {jsonData}")
					return
			else:
				logging.info(f"Response data received. Payload: : {jsonData}")		
				
		else:
			logging.info(f"Response data received. Payload: : {jsonData}")
	
	def _onPostResponse(self, response):
		"""Handle POST response"""
		if not response:
			logging.warning("Async POST response invalid. Ignoring.")
			return
		
		logging.info("Async POST response received.")
		
		responseData = response.payload.decode("utf-8")
		
		logging.info(f"Response data received. Payload: {responseData}")
	
	def _onPutResponse(self, response):
			"""Handle PUT response"""
			if not response:
				logging.warning("Async PUT response invalid. Ignoring.")
				return
			
			logging.info("Async PUT response received.")
			
			responseData = response.payload.decode("utf-8")
			
			logging.info(f"Response data received. Payload: {responseData}")
   
	# Initialize event loop for async operations
	def _initEventLoop(self):
		"""Initialize event loop for async operations"""
		def startEventLoop(loop):
			asyncio.set_event_loop(loop)
			loop.run_forever()

		self._eventLoopThread = asyncio.new_event_loop()
		self._executionThread = threading.Thread(
			target = startEventLoop, 
			args = (self._eventLoopThread,), 
			daemon = True
		)

		self._executionThread.start()

		future = asyncio.run_coroutine_threadsafe(
			self._initClientContext(), 
			self._eventLoopThread
		)

		future.result()

	async def _initClientContext(self):
		"""Initialize client context"""
		self.clientContext = await Context.create_client_context()

	# Public interface method implementations
	def sendDiscoveryRequest(self, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""Send discovery request"""
		logging.info("Discovering remote resources...")
		
		resourcePath = self._createResourcePath(None, ".well-known/core")
			
		logging.info(f"Issuing Async GET - DISCOVERY to path: {resourcePath}")
			
		future = asyncio.run_coroutine_threadsafe(
			self._handleDiscoveryRequest(resourcePath),
			self._eventLoopThread
		)

		return future.result()

	def sendDeleteRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""Send DELETE request"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			logging.info(f"Issuing Async DELETE to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handleDeleteRequest(resourcePath, enableCON),
				self._eventLoopThread
			)

			return future.result()
		else:
			logging.warning("Can't issue Async DELETE - no path provided.")
			return False

	def sendGetRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""Send GET request"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			logging.info(f"Issuing Async GET to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handleGetRequest(resourcePath, enableCON),
				self._eventLoopThread
			)

			return future.result()
		else:
			logging.warning("Can't issue Async GET - no path provided.")
			return False

	def sendPostRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""Send POST request"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			logging.info(f"Issuing Async POST to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handlePostRequest(resourcePath, payload, enableCON),
				self._eventLoopThread
			)

			return future.result()
		else:
			logging.warning("Can't issue Async POST - no path provided.")
			return False

	def sendPutRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
			"""Send PUT request"""
			if resource or name:
				resourcePath = self._createResourcePath(resource, name)
				
				logging.info(f"Issuing Async PUT to path: {resourcePath}")
				
				future = asyncio.run_coroutine_threadsafe(
					self._handlePutRequest(resourcePath, payload, enableCON),
					self._eventLoopThread
				)

				return future.result()
			else:
				logging.warning("Can't issue Async PUT - no path provided.")
				return False
  
	def startObserver(self, resource: ResourceNameEnum = None, name: str = None, ttl: int = IRequestResponseClient.DEFAULT_TTL) -> bool:
		"""Start observer"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
		
			if resourcePath in self.observeTasks:
				logging.warning(f"Already observing resource {resourcePath}. Ignoring start observe request.")
				return False

			fullPath = self.uriPath + resourcePath

			task = asyncio.run_coroutine_threadsafe(
				self._handleStartObserveRequest(fullPath),
				self._eventLoopThread
			)

			self.observeTasks[resourcePath] = task  # Store in Tasks

			logging.info(f"Started observing: {resourcePath}")
			return True
		else:
			logging.warning("Can't issue Async OBSERVE - GET - no path provided.")
			return False

	def stopObserver(self, resource: ResourceNameEnum = None, name: str = None) -> bool:
		"""Stop observer"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			if resourcePath not in self.observeTasks:  # Check Tasks
				logging.warning(f"Resource {resourcePath} not being observed. Ignoring stop observe request.")
				return False
			
			task = self.observeTasks[resourcePath]  # Get from Tasks
			task.cancel()

			cleanup_future = asyncio.run_coroutine_threadsafe(
				self._handleStopObserveRequest(resourcePath, ignoreErr = True),
				self._eventLoopThread
			)

			try:
				cleanup_future.result(timeout = 5.0)
				logging.info(f"Stopped observing: {resourcePath}")
				del self.observeTasks[resourcePath]  # Delete from Tasks
				return True
			
			except Exception as e:
				logging.error(f"Error stopping observation: {e}")
				return False
		else:
			logging.warning("Can't cancel OBSERVE - GET - no path provided.")
			return False
	
	def disconnectClient(self):
		"""
		Shuts down the CoAP client connection and stops the event loop.
		"""
		logging.info("Disconnecting CoAP client...")
		
		try:
			if hasattr(self, '_eventLoopThread') and self._eventLoopThread.is_running():
				logging.debug("Scheduling async client shutdown.")
				
				# Schedule the async shutdown
				future = asyncio.run_coroutine_threadsafe(
					self._shutdownClient(),
					self._eventLoopThread
				)
				
				# Wait for the async shutdown to complete
				future.result(timeout=5.0) 
				
				# Stop the event loop
				logging.debug("Stopping event loop thread.")
				self._eventLoopThread.call_soon_threadsafe(self._eventLoopThread.stop)
			
			if hasattr(self, '_executionThread') and self._executionThread.is_alive():
				logging.debug("Waiting for execution thread to join...")
				self._executionThread.join(timeout=2.0)
    
    	# Ensure event loop is closed
			if hasattr(self, '_eventLoopThread') and not self._eventLoopThread.is_closed():
					logging.debug("Closing event loop.")
					self._eventLoopThread.close()

			logging.info("CoAP client disconnected successfully.")

		except Exception as e:
			logging.error(f"Error during CoAP client disconnection: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)
