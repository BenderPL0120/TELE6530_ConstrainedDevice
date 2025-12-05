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

  def __init__(self, dataMsgListener: IDataMessageListener = None):
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
    self.ledDisplayActuator = None
    self.windowActuator = None
    self.buzzerActuator = None

    if self.useEmulator:
      logging.info("Emulators will be used for actuators.")
    else:
      logging.info("Simulators will be used for actuators.")

    self._initEnvironmentalActuationTasks()

  def sendActuatorCommand(self, data: ActuatorData) -> ActuatorData:
    if not data or data.isResponseFlagEnabled():
      logging.warning("Invalid ActuatorData received. Ignoring.")
      return None

    if data.getLocationID() != self.locationID:
      logging.warning(
        "Location ID mismatch. Ignoring actuation command. Expected: %s, Got: %s",
        self.locationID, data.getLocationID())
      return None

    logging.info(
      "Actuator command received for location ID %s. Processing...", self.locationID)

    actuatorType = data.getTypeID()
    responseData = None

    if actuatorType == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE and self.humidifierActuator:
      responseData = self.humidifierActuator.updateActuator(data)
    elif actuatorType == ConfigConst.HVAC_ACTUATOR_TYPE and self.hvacActuator:
      responseData = self.hvacActuator.updateActuator(data)
    elif actuatorType == ConfigConst.LED_DISPLAY_ACTUATOR_TYPE and self.ledDisplayActuator:
      responseData = self.ledDisplayActuator.updateActuator(data)
    elif actuatorType == ConfigConst.WINDOW_ACTUATOR_TYPE and self.windowActuator:
      responseData = self.windowActuator.updateActuator(data)
    elif actuatorType == ConfigConst.BUZZER_ACTUATOR_TYPE and self.buzzerActuator:
      responseData = self.buzzerActuator.updateActuator(data)
    else:
      logging.error(
        "No valid actuator found for type ID: %s. Command ignored.", str(actuatorType))

    return responseData

  def setDataMessageListener(self, listener: IDataMessageListener) -> bool:
    if listener:
      self.dataMsgListener = listener
      return True
    return False

  def getWindowActuator(self):
    """
		Returns the window actuator instance for external refresh calls.
		"""
    return self.windowActuator

  def _initEnvironmentalActuationTasks(self):
    if not self.useEmulator:
      logging.info("Initializing simulated environmental actuators...")
      self.humidifierActuator = HumidifierActuatorSimTask()
      self.hvacActuator = HvacActuatorSimTask()
      self.windowActuator = None
    else:
      logging.info("Initializing emulated environmental actuators...")

      hueModule = import_module('programmingtheiot.cda.emulated.HumidifierEmulatorTask', 'HumidifierEmulatorTask')
      hueClazz = getattr(hueModule, 'HumidifierEmulatorTask')
      self.humidifierActuator = hueClazz()

      hveModule = import_module('programmingtheiot.cda.emulated.HvacEmulatorTask', 'HvacEmulatorTask')
      hveClazz = getattr(hveModule, 'HvacEmulatorTask')
      self.hvacActuator = hveClazz()

      leDisplayModule = import_module('programmingtheiot.cda.emulated.LedDisplayEmulatorTask', 'LedDisplayEmulatorTask')
      leClazz = getattr(leDisplayModule, 'LedDisplayEmulatorTask')
      self.ledDisplayActuator = leClazz()

      windowModule = import_module('programmingtheiot.cda.emulated.WindowDisplayEmulatorTask', 'WindowDisplayEmulatorTask')
      windowClazz = getattr(windowModule, 'WindowDisplayEmulatorTask')
      self.windowActuator = windowClazz()

      buzzerModule = import_module('programmingtheiot.cda.emulated.BuzzerEmulatorTask', 'BuzzerEmulatorTask')
      buzzerClazz = getattr(buzzerModule, 'BuzzerEmulatorTask')
      self.buzzerActuator = buzzerClazz()