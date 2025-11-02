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

import asyncio
import time
import traceback
import threading

import aiocoap
import aiocoap.resource as resource

from aiocoap.resource import Resource

from typing import Optional, Dict, Any
from contextlib import suppress

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.cda.connection.handlers.GetTelemetryResourceHandler import GetTelemetryResourceHandler
from programmingtheiot.cda.connection.handlers.GetSystemPerformanceResourceHandler import GetSystemPerformanceResourceHandler
from programmingtheiot.cda.connection.handlers.UpdateActuatorResourceHandler import UpdateActuatorResourceHandler

class CoapServerAdapter():
	"""
	Definition for a CoAP communications server using aiocoap, with embedded test functions.
	
	"""

	def __init__(self, dataMsgListener: IDataMessageListener = None):
		"""
		Constructor for CoapServerAdapter

		@param dataMsgListener: The data message listener for handling callbacks
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		
		self.host = self.config.getProperty(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		self.port = self.config.getInteger(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_COAP_PORT)
		
		self.serverUri = f"coap://{self.host}:{self.port}"

		self.coapServer   = None
		self.rootResource = None
		
		self._serverTask: Optional[asyncio.Task] = None
		self._eventLoopThread: Optional[asyncio.AbstractEventLoop] = None
		self._executionThread: Optional[threading.Thread] = None
		self._shutdownEvent: Optional[asyncio.Event] = None
		self._shutdownFuture: Optional[asyncio.Future] = None

		self._initServer()
		
		logging.info(f" CoAP Server configured at {self.serverUri}")

	def _initServer(self):
		"""
		Initialize the CoAP server and register default resources
		"""
		try:
			# Resource tree creation - lib-specific (this line of code assumes use of aiocoap)
			self.rootResource = resource.Site()
			
			# Necessary to ensure discovery will function
			self.rootResource.add_resource(
				['.well-known', 'core'],
				resource.WKCResource(self.rootResource.get_resources_as_linkheader))
			
			# Register UpdateActuator resources
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.HUMIDIFIER_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.HUMIDIFIER_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener))
			
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.HVAC_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.HVAC_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener))

			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.LED_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.LED_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener))
			
			# Register System Performance resource
			sysPerfDataListener = GetSystemPerformanceResourceHandler(
				name=ConfigConst.SYSTEM_PERF_MSG,
				dataMsgListener=self.dataMsgListener)
			
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
				resource=sysPerfDataListener)
			
			# Register Telemetry resource
			sensorDataListener = GetTelemetryResourceHandler(
				name=ConfigConst.SENSOR_MSG,
				dataMsgListener=self.dataMsgListener)
			
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
				resource=sensorDataListener)
			
			# Register the callbacks with the data message listener instance
			if self.dataMsgListener:
				self.dataMsgListener.setTelemetryDataListener(listener=sensorDataListener)
				self.dataMsgListener.setSystemPerformanceDataListener(listener=sysPerfDataListener)
			
			logging.info("Created CoAP server with default resources.")
			
		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning(f"Failed to create  CoAP Server at {self.serverUri}")

	def addResource(self, resourcePath: ResourceNameEnum = None, endName: str = None, resource: Resource = None):
		"""
		Add a resource to the CoAP server

		@param resourcePath: The resource path enum
		@param endName: Optional end name for the resource
		@param resource: The resource handler to add
		"""
		if resourcePath and resource:
			uriPath = resourcePath.value
			
			if endName:
				uriPath = uriPath + '/' + endName
				
			resourceList = uriPath.split('/')
			
			if not self.rootResource:
				self.rootResource = resource.Site()
				
			logging.info(f"Adding resource to server: {resourceList}")

			try:
				self.rootResource.add_resource(resourceList, resource)
				
			except Exception as e:
				logging.error(f"Failed to add resource to server: {resourceList}")
				traceback.print_exception(type(e), e, e.__traceback__)
		else:
			logging.warning(f"No resource provided for path: {uriPath if resourcePath else 'None'}")

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		"""
		Set the data message listener after initialization

		@param listener: The data message listener
		@return: True if successful, False otherwise
		"""
		if listener:
			self.dataMsgListener = listener
			logging.info("Data message listener updated")
			return True
		else:
			logging.warn("Null listener provided")
			return False

	def startServer(self) -> bool:
		"""
		Start the CoAP server

		@return: True if successful, False otherwise
		"""
		if self._serverTask and not self._serverTask.done():
			logging.warning("Server already running. Ignoring start request.")
			return False
		
		if not self.rootResource:
			logging.error("No resources configured. Nothing for server to do.")
			return False
		
		try:
			logging.info(f"Starting  CoAP Server at {self.serverUri}")

			self._eventLoopThread = asyncio.new_event_loop()
			self._shutdownEvent = asyncio.Event()

			self._executionThread = threading.Thread(
				target = self._runServerTask,
				daemon = True,
				name = "-CoAP-Server-Thread")
			
			self._executionThread.start()

			# Wait a fraction of a second so server can spin up
			time.sleep(0.5)

			logging.info(f" CoAP Server started at {self.serverUri}")

			return True
		
		except Exception as e:
			logging.error(f"Failed to start  CoAP Server at {self.serverUri}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False

	def stopServer(self) -> bool:
		"""
		Stop the CoAP server

		@return: True if successful, False otherwise
		"""
		if not self._eventLoopThread or not self._serverTask:
			logging.warning(" CoAP Server not yet running. Ignoring stop request.")
			return False

		try:
			logging.info(f"Shutting down  CoAP Server at {self.serverUri}")

			if self._eventLoopThread.is_running():
				asyncio.run_coroutine_threadsafe(
					self._shutdownServer(),
					self._eventLoopThread)

			for _ in range(5):
				if self._serverTask.done():
					break

				time.sleep(1.0)

			if self._eventLoopThread.is_running():
				self._eventLoopThread.call_soon_threadsafe(self._eventLoopThread.stop)

			logging.info(f" CoAP Server shutdown: {self.serverUri}")

			return True
		
		except Exception as e:
			logging.error(f"Failed to shutdown  CoAP Server at {self.serverUri}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False

	def _runServerTask(self):
		"""
		Internal method to run the server task in a separate thread
		"""
		logging.info("Starting  CoAP Server task...")

		asyncio.set_event_loop(self._eventLoopThread)

		try:
			self._eventLoopThread.run_until_complete(self._runServer())

		except asyncio.CancelledError:
			logging.info("Server task cancelled.")

		except Exception as e:
			logging.exception(f"Error starting  CoAP Server task: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)

		finally:
			pendingTasks = asyncio.all_tasks(self._eventLoopThread)

			try:
				for task in pendingTasks:
					task.cancel()

				if pendingTasks:
					self._eventLoopThread.run_until_complete(
						asyncio.gather(*pendingTasks, return_exceptions=True))

				self._eventLoopThread.close()

			except Exception as e:
				logging.exception(f" CoAP Server event loop thread exception: {e}")
				traceback.print_exception(type(e), e, e.__traceback__)

			logging.info("Successfully closed  CoAP Server event loop.")

	async def _runServer(self):
		"""
		Internal async method to run the server
		"""
		if self.rootResource:
			logging.info("Creating  CoAP Server context...")

			try:
				bindTuple = (self.host, self.port)
				
				self.coapServer = \
					await aiocoap.Context.create_server_context(
						site=self.rootResource,
						bind=bindTuple)

				logging.info("Initializing  CoAP Server Task...")

				self._serverTask = asyncio.current_task()

				await self._keepServerRunning()

			except asyncio.CancelledError:
				logging.info("Server coroutine cancelled.")

			except Exception as e:
				logging.exception(f"Failed to spin up  CoAP Server task: {e}")

		else:
			logging.warning("Root resource not yet created. Can't start server.")

	async def _keepServerRunning(self):
		"""
		Keep the server running until shutdown is requested
		"""
		try:
			logging.info("Initializing  CoAP Server shutdown future...")

			self._shutdownFuture = asyncio.get_running_loop().create_future()

			await self._shutdownFuture

		except asyncio.CancelledError:
			logging.info("Server keep-alive cancelled.")

		except Exception as e:
			logging.info(" CoAP Server future cancelled [OK]")

	async def _shutdownServer(self):
		"""
		Internal async method to shutdown the server
		"""
		try:
			if self.coapServer:
				logging.info(f"Shutting down  CoAP Server at {self.serverUri}")

				await self.coapServer.shutdown()

				self.coapServer = None

				if hasattr(self, "_shutdownFuture") and not self._shutdownFuture.done():
					self._shutdownFuture.set_result(None)

				if self._serverTask and not self._serverTask.done():
					self._serverTask.cancel()

					with suppress(asyncio.exceptions.CancelledError):
						await self._serverTask

				logging.info(" CoAP Server shutdown completed.")

		except Exception as e:
			logging.warning("Failed to shutdown  CoAP server.")
			traceback.print_exception(type(e), e, e.__traceback__)