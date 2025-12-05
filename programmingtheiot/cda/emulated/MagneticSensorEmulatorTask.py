#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#

import logging
import math

from programmingtheiot.data.SensorData import SensorData

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask

from pisense import SenseHAT


class MagneticSensorEmulatorTask(BaseSensorSimTask):
	"""
	Magnetic sensor emulator task.
	Uses IMU data to retrieve Yaw (heading) angle.
	Robust version: Handles NoneType sensor values gracefully.
	"""

	def __init__(self):
		super( \
			MagneticSensorEmulatorTask, self).__init__( \
			name=ConfigConst.MAGNETIC_SENSOR_NAME, \
			typeID=ConfigConst.MAGNETIC_SENSOR_TYPE)

		enableEmulation = \
			ConfigUtil().getBoolean( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.ENABLE_EMULATOR_KEY)

		self.sh = SenseHAT(emulate=enableEmulation)

	def generateTelemetry(self) -> SensorData:
		sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
		sensorVal = 0.0

		try:
			# Try to get orientation (yaw) first
			if hasattr(self.sh.imu, 'orientation') and self.sh.imu.orientation is not None:
				orientation = self.sh.imu.orientation
				if orientation.yaw is not None:
					sensorVal = orientation.yaw
					logging.debug(f"Orientation Yaw read: {sensorVal:.2f}")
				else:
					# if
					raise AttributeError("Orientation yaw is None")
			else:
				raise AttributeError("Orientation attribute missing or None")

		except (AttributeError, TypeError):
			logging.warning("Orientation not available, using compass fallback")

			try:
				compass = self.sh.imu.compass

				if compass is not None and compass.x is not None and compass.y is not None:
					# Calculate raw angle
					angle_rad = math.atan2(compass.y, compass.x)
					angle_deg = math.degrees(angle_rad)

					# Convert to heading
					raw_heading = -angle_deg + 90.0

					# Calibration Offset
					CALIBRATION_OFFSET = 95.0
					sensorVal = raw_heading - CALIBRATION_OFFSET

					# Normalize to 0 - 360
					sensorVal = (sensorVal + 360) % 360

					# Convert to -180 to +180
					if sensorVal > 180:
						sensorVal -= 360

					logging.debug(f"Raw: {raw_heading:.2f}, Corrected: {sensorVal:.2f}")
				else:
					logging.warning("Compass data is None (Simulator not ready?). Returning 0.0")
					sensorVal = 0.0

			except Exception as e:
				logging.error(f"Error reading Compass data: {e}")
				sensorVal = 0.0

		except Exception as e:
			logging.error(f"Error reading IMU data for Magnetic sensor: {e}")
			sensorVal = 0.0

		sensorData.setValue(sensorVal)
		self.latestSensorData = sensorData
		return sensorData