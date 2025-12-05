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
from programmingtheiot.cda.emulated.OrientationSensorEmulatorTask import OrientationSensorEmulatorTask


class OrientationSensorEmulatorTaskTest(unittest.TestCase):
	"""
	Test case for OrientationSensorEmulatorTask.
	"""

	@classmethod
	def setUpClass(self):
		logging.basicConfig(format='%(asctime)s:%(module)s:%(levelname)s:%(message)s', level=logging.DEBUG)
		logging.info("Testing OrientationSensorEmulatorTask class...")
		self.oSimTask = OrientationSensorEmulatorTask()

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testReadEmulator(self):
		# Reading 1
		sd1 = self.oSimTask.generateTelemetry()

		if sd1:
			self.assertEqual(sd1.getTypeID(), ConfigConst.ORIENTATION_SENSOR_TYPE)
			# Pitch value can be negative or positive depending on simulated rotation
			logging.info("SensorData 1: %f - %s", sd1.getValue(), str(sd1))
		else:
			self.fail("SensorData is None.")

		# Wait a bit
		sleep(2)

		# Reading 2
		sd2 = self.oSimTask.generateTelemetry()

		if sd2:
			self.assertEqual(sd2.getTypeID(), ConfigConst.ORIENTATION_SENSOR_TYPE)
			logging.info("SensorData 2: %f - %s", sd2.getValue(), str(sd2))
		else:
			self.fail("SensorData is None.")


if __name__ == "__main__":
	unittest.main()