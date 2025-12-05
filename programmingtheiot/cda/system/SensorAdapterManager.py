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

from apscheduler.schedulers.background import BackgroundScheduler

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator
from programmingtheiot.cda.sim.HumiditySensorSimTask import HumiditySensorSimTask
from programmingtheiot.cda.sim.TemperatureSensorSimTask import TemperatureSensorSimTask
from programmingtheiot.cda.sim.PressureSensorSimTask import PressureSensorSimTask

class SensorAdapterManager(object):
  """
	Shell representation of class for student implementation.

	"""

  def __init__(self):
    self.configUtil = ConfigUtil()

    self.pollRate = self.configUtil.getInteger(
      section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.POLL_CYCLES_KEY,
      defaultVal=ConfigConst.DEFAULT_POLL_CYCLES)

    self.useEmulator = self.configUtil.getBoolean(
      section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_EMULATOR_KEY)

    self.locationID = self.configUtil.getProperty(
      section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.DEVICE_LOCATION_ID_KEY, defaultVal=ConfigConst.NOT_SET)

    if self.pollRate <= 0:
      self.pollRate = ConfigConst.DEFAULT_POLL_CYCLES

    self.scheduler = BackgroundScheduler()
    self.scheduler.add_job(
      self.handleTelemetry, 'interval', seconds=self.pollRate, max_instances=2, coalesce=True, misfire_grace_time=15)

    self.dataMsgListener = None
    self.humidityAdapter = None
    self.pressureAdapter = None
    self.tempAdapter = None
    self.orientationAdapter = None
    self.magneticAdapter = None

    self._initEnvironmentalSensorTasks()

  def handleTelemetry(self):
    try:
      humidityData = self.humidityAdapter.generateTelemetry()
      pressureData = self.pressureAdapter.generateTelemetry()
      tempData = self.tempAdapter.generateTelemetry()

      humidityData.setLocationID(self.locationID)
      pressureData.setLocationID(self.locationID)
      tempData.setLocationID(self.locationID)

      logging.debug(f'Generated humidity data: {humidityData.getValue()}')
      logging.debug(f'Generated pressure data: {pressureData.getValue()}')
      logging.debug(f'Generated temp data: {tempData.getValue()}')

      if self.dataMsgListener:
        self.dataMsgListener.handleSensorMessage(humidityData)
        self.dataMsgListener.handleSensorMessage(pressureData)
        self.dataMsgListener.handleSensorMessage(tempData)

      # handle orientation data
      if self.orientationAdapter:
        orientationData = self.orientationAdapter.generateTelemetry()
        orientationData.setLocationID(self.locationID)

        logging.debug(f'Generated orientation data: {orientationData.getValue()}')

        if self.dataMsgListener:
          self.dataMsgListener.handleSensorMessage(orientationData)

      # handle magnetic data
      if self.magneticAdapter:
        magneticData = self.magneticAdapter.generateTelemetry()
        magneticData.setLocationID(self.locationID)

        logging.debug(f'Generated magnetic data: {magneticData.getValue()}')

        if self.dataMsgListener:
          self.dataMsgListener.handleSensorMessage(magneticData)

    except Exception as e:
      logging.error(f"Error in handleTelemetry: {e}", exc_info=True)

  def setDataMessageListener(self, listener: IDataMessageListener) -> bool:
    if listener:
      self.dataMsgListener = listener
      return True
    return False

  def startManager(self):
    logging.info("Started SensorAdapterManager.")

    if not self.scheduler.running:
      self.scheduler.start()
      return True
    else:
      logging.warning("SensorAdapterManager scheduler already started. Ignoring.")
      return False

  def stopManager(self):
    logging.info("Stopped SensorAdapterManager.")

    try:
      if self.scheduler.running:
        self.scheduler.shutdown()
        return True
      else:
        logging.warning("SensorAdapterManager scheduler already stopped. Ignoring.")
        return False
    except:
      logging.exception("Failed to shut down SensorAdapterManager scheduler.")
      return False

  def _initEnvironmentalSensorTasks(self):
    humidityFloor = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.HUMIDITY_SIM_FLOOR_KEY,
      defaultVal=SensorDataGenerator.LOW_NORMAL_ENV_HUMIDITY)
    humidityCeiling = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.HUMIDITY_SIM_CEILING_KEY,
      defaultVal=SensorDataGenerator.HI_NORMAL_ENV_HUMIDITY)

    pressureFloor = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.PRESSURE_SIM_FLOOR_KEY,
      defaultVal=SensorDataGenerator.LOW_NORMAL_ENV_PRESSURE)
    pressureCeiling = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.PRESSURE_SIM_CEILING_KEY,
      defaultVal=SensorDataGenerator.HI_NORMAL_ENV_PRESSURE)

    tempFloor = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.TEMP_SIM_FLOOR_KEY,
      defaultVal=SensorDataGenerator.LOW_NORMAL_INDOOR_TEMP)
    tempCeiling = self.configUtil.getFloat(
      section=ConfigConst.CONSTRAINED_DEVICE,
      key=ConfigConst.TEMP_SIM_CEILING_KEY,
      defaultVal=SensorDataGenerator.HI_NORMAL_INDOOR_TEMP)

    if not self.useEmulator:
      logging.info("Simulators will be used.")

      self.dataGenerator = SensorDataGenerator()

      humidityData = self.dataGenerator.generateDailyEnvironmentHumidityDataSet(
        minValue=humidityFloor, maxValue=humidityCeiling, useSeconds=False)
      pressureData = self.dataGenerator.generateDailyEnvironmentPressureDataSet(
        minValue=pressureFloor, maxValue=pressureCeiling, useSeconds=False)
      tempData = self.dataGenerator.generateDailyIndoorTemperatureDataSet(
        minValue=tempFloor, maxValue=tempCeiling, useSeconds=False)

      self.humidityAdapter = HumiditySensorSimTask(dataSet=humidityData)
      self.pressureAdapter = PressureSensorSimTask(dataSet=pressureData)
      self.tempAdapter = TemperatureSensorSimTask(dataSet=tempData)

      # Set to None in non-emulator mode
      self.orientationAdapter = None
      self.magneticAdapter = None

    else:
      logging.info("Emulators will be used.")

      heModule = import_module('programmingtheiot.cda.emulated.HumiditySensorEmulatorTask',
                               'HumiditySensorEmulatorTask')
      heClazz = getattr(heModule, 'HumiditySensorEmulatorTask')
      self.humidityAdapter = heClazz()

      peModule = import_module('programmingtheiot.cda.emulated.PressureSensorEmulatorTask',
                               'PressureSensorEmulatorTask')
      peClazz = getattr(peModule, 'PressureSensorEmulatorTask')
      self.pressureAdapter = peClazz()

      teModule = import_module('programmingtheiot.cda.emulated.TemperatureSensorEmulatorTask',
                               'TemperatureSensorEmulatorTask')
      teClazz = getattr(teModule, 'TemperatureSensorEmulatorTask')
      self.tempAdapter = teClazz()

      oeModule = import_module('programmingtheiot.cda.emulated.OrientationSensorEmulatorTask',
                               'OrientationSensorEmulatorTask')
      oeClazz = getattr(oeModule, 'OrientationSensorEmulatorTask')
      self.orientationAdapter = oeClazz()

      meModule = import_module('programmingtheiot.cda.emulated.MagneticSensorEmulatorTask',
                               'MagneticSensorEmulatorTask')
      meClazz = getattr(meModule, 'MagneticSensorEmulatorTask')
      self.magneticAdapter = meClazz()