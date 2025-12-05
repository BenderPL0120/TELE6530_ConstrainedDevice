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
import math

from programmingtheiot.data.SensorData import SensorData

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask

from pisense import SenseHAT

class OrientationSensorEmulatorTask(BaseSensorSimTask):
	"""
	Orientation sensor emulator task.
	Uses accelerometer data to calculate pitch angle.
	"""

	def __init__(self):
		super(
			OrientationSensorEmulatorTask, self).__init__(
			name=ConfigConst.ORIENTATION_SENSOR_NAME,
			typeID=ConfigConst.ORIENTATION_SENSOR_TYPE)

		enableEmulation = \
			ConfigUtil().getBoolean(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.ENABLE_EMULATOR_KEY)

		self.sh = SenseHAT(emulate=enableEmulation)

	def generateTelemetry(self) -> SensorData:
		sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())

		try:
			if hasattr(self.sh.imu, 'orientation'):
				orientation = self.sh.imu.orientation
				sensorVal = orientation.pitch
			else:
				# Fallback: calculate pitch from accelerometer
				# accel returns a named tuple containing x, y, z components (in Gs)
				accel = self.sh.imu.accel

				# Pitch = atan(x / sqrt(y^2 + z^2))
				dist = math.sqrt(accel.y * accel.y + accel.z * accel.z)
				sensorVal = -math.degrees(math.atan2(accel.x, dist))

		except Exception as e:
			logging.error(f"Error reading IMU data: {e}")
			sensorVal = 0.0

		sensorData.setValue(sensorVal)
		self.latestSensorData = sensorData

		return sensorData