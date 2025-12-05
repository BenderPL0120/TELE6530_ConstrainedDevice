#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#

import logging
import unittest
from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.cda.emulated.MagneticSensorEmulatorTask import MagneticSensorEmulatorTask


class MagneticSensorEmulatorTaskTest(unittest.TestCase):
	"""
	Test case for MagneticSensorEmulatorTask (Compass/Yaw).
	"""

	@classmethod
	def setUpClass(self):
		logging.basicConfig(format='%(asctime)s:%(module)s:%(levelname)s:%(message)s', level=logging.DEBUG)
		logging.info("Testing MagneticSensorEmulatorTask class...")
		self.mSimTask = MagneticSensorEmulatorTask()

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testReadEmulator(self):
		sd = self.mSimTask.generateTelemetry()

		if sd:
			self.assertEqual(sd.getTypeID(), ConfigConst.MAGNETIC_SENSOR_TYPE)
			val = sd.getValue()

			logging.info("Magnetic Heading: %f - %s", val, str(sd))

			# Basic validation: Heading should typically be within -180 to 180 or 0 to 360
			# Your implementation converts >180 to negative, so checking absolute bounds
			self.assertTrue(-180.0 <= val <= 360.0, "Heading value is out of expected range")

		else:
			self.fail("SensorData is None.")

		sleep(2)

		sd2 = self.mSimTask.generateTelemetry()
		if sd2:
			logging.info("Magnetic Heading 2: %f", sd2.getValue())


if __name__ == "__main__":
	unittest.main()